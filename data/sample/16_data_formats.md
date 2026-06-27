# Nimbus Data Formats and Schemas

Nimbus stores events as schema-flexible JSON. Understanding how Nimbus represents
data internally helps you write efficient queries and design good ingest pipelines.

## Event structure

Every event stored in Nimbus is a flat or nested JSON object. Nimbus adds the
following reserved fields automatically at ingest time:

| Field           | Type             | Description                                        |
|-----------------|------------------|----------------------------------------------------|
| `_received_at`  | ISO-8601 string  | UTC timestamp when the IGW accepted the event.     |
| `_ingest_id`    | UUID string      | Unique identifier for this event within Nimbus.    |
| `_dataset`      | string           | Name of the dataset this event belongs to.         |

Reserved fields are prefixed with `_`. You must not send fields with this prefix
in your own payloads; they will be silently overwritten.

## Nested objects and arrays

The Query Engine supports querying nested fields using dot notation:

```sql
SELECT payload.user.id, payload.tags[0]
FROM my-dataset
WHERE payload.country = 'DE'
```

Deeply nested structures are supported up to 5 levels. Arrays can be unnested
with the `UNNEST` function:

```sql
SELECT _received_at, tag
FROM my-dataset, UNNEST(tags) AS tag
```

## Type inference

Nimbus infers column types from the first 1,000 events ingested after a dataset
is created. Inferred types are: `string`, `number`, `boolean`, `object`,
`array`, and `null`. If a field appears with conflicting types (e.g. sometimes
a string, sometimes a number), it is stored and queried as `string`.

You can pin types explicitly via the Schema Registry (Scale and Enterprise plans)
to avoid inference surprises.

## Schema Registry

The Schema Registry lets you define a JSON Schema for a dataset. When strict
mode is on, events that do not conform are rejected at the IGW (HTTP 422). The
Schema Registry also drives IDE autocompletion for the `nimbus-sdk` and the
`nbx` CLI.

Register a schema:
```bash
nbx schema set my-dataset --file schema.json
```

Retrieve the current schema:
```bash
nbx schema get my-dataset
```

## Numeric precision

Nimbus stores all numbers as 64-bit IEEE 754 doubles. Integers larger than
2^53 lose precision. For high-precision integer IDs (e.g. 64-bit user IDs),
send them as strings.

## Timestamps

Any field ending in `_at`, `_time`, or `_ts` is automatically detected as a
timestamp and indexed for fast range queries. You can suppress auto-detection
by prefixing the field name with `raw_` (e.g. `raw_created_at`).

## Maximum event size

A single event must not exceed 64 KB. Larger payloads should be chunked by the
producer or stored externally (e.g. in S3) with only a reference URL in Nimbus.
