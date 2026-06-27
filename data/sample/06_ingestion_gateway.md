# Nimbus Ingestion Gateway (IGW) — Deep Dive

The Ingestion Gateway is the single public entry point for all writes to Nimbus.
It runs as a stateless cluster behind a global anycast IP, so clients always
connect to the nearest point of presence.

## Protocols

The IGW accepts writes over two protocols:

- **HTTP/1.1 and HTTP/2** — events are posted as newline-delimited JSON (NDJSON)
  to `/v1/ingest/<dataset>`. The `Content-Type` must be
  `application/x-ndjson`.
- **gRPC** — the `NimbusIngest` service defined in `nimbus.proto`. Prefer gRPC
  for high-throughput producers because it multiplexes over a single connection
  and avoids HTTP header overhead.

Both protocols require the `Authorization: Bearer <API_KEY>` header. The API key
must carry the `writer` or `admin` role.

## Batching and payload limits

A single ingest call may contain up to 10,000 events or 10 MB of payload,
whichever is smaller. Larger batches must be split client-side. The `nbx ingest`
command handles splitting automatically when reading from a file.

Events are accepted as an array of arbitrary JSON objects. The IGW stamps each
event with a server-side `_received_at` field (UTC ISO-8601) before forwarding
to storage. Client-supplied `_received_at` fields are silently overwritten.

## Rate limiting

Rate limits are enforced per dataset, not per API key. When the ingestion rate
exceeds the plan limit the IGW returns **HTTP 429** with a
`Retry-After: <seconds>` header. The recommended backoff strategy is truncated
exponential: start at 1 second, double on each retry, cap at 60 seconds.

| Plan       | Limit              |
|------------|--------------------|
| Free       | 100 events/sec     |
| Scale      | 10,000 events/sec  |
| Enterprise | Contractual        |

Burst allowances: the IGW permits up to 2× the plan limit for up to 5 seconds
before rate limiting kicks in. This absorbs short traffic spikes without
requiring clients to implement complex shaping.

## Compression

Payloads may be gzip-compressed. Set `Content-Encoding: gzip` and the IGW
decompresses before parsing. Compressed payloads are not subject to the 10 MB
raw-byte limit; the limit applies to the compressed size on the wire.

## Acknowledgement and durability

A successful response (`HTTP 200` or gRPC `OK`) guarantees that the events have
been written to at least two availability zones. The IGW does not guarantee
ordering across concurrent requests from different clients to the same dataset.

## Schema validation

By default the IGW accepts any valid JSON object. Optional strict-mode schema
validation can be enabled per dataset from the console or via the API. When
strict mode is on, events that fail schema validation are rejected with
`HTTP 422` and a field-level error body; they are never silently dropped.
