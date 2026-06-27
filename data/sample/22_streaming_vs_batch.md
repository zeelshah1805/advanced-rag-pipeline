# Streaming vs Batch Ingestion in Nimbus

Nimbus supports both streaming and batch ingestion patterns through the same
Ingestion Gateway endpoint. The choice affects latency, throughput, and cost.

## Streaming ingestion

In streaming mode, producers send events as they occur, typically in small
batches of 1–1,000 events flushed every few seconds. This gives the lowest
event-to-query latency (events are queryable within 30 seconds of acceptance).

Recommended when:
- You need near-real-time visibility (dashboards, alerting).
- Your producer is a message queue or stream (Kafka, Kinesis, Pub/Sub).
- Event volume is continuous and relatively steady.

The `nimbus-sdk` `StreamingIngestor` and the Kafka Connector are designed for
this pattern.

## Batch ingestion

In batch mode, producers accumulate events and send them in large periodic
payloads (e.g. hourly dumps of CSV/NDJSON files). This minimises API call
overhead and is well-suited to ETL pipelines.

Recommended when:
- Source data arrives in bulk files (nightly exports, log archives).
- Latency requirements are measured in hours, not seconds.
- You are migrating historical data into Nimbus.

Use `nbx ingest --file <path>` for batch file ingestion; `nbx` handles splitting
files that exceed the 10,000-event / 10 MB per-call limit automatically.

## Hybrid: micro-batching

The most common production pattern is micro-batching: buffer events for 1–5
seconds client-side, then send in batches of a few hundred to a few thousand
events. This balances latency (events queryable within ~35 seconds) against
IGW call overhead.

The `StreamingIngestor` in the Python and Node.js SDKs implements micro-batching
with configurable `flush_interval` and `max_batch` parameters.

## Ingestion latency

| Pattern        | Typical event-to-query latency |
|----------------|-------------------------------|
| Streaming (1s flush) | 30–35 seconds           |
| Micro-batch (5s flush) | 35–40 seconds         |
| Batch (hourly file)  | Up to 1 hour + 30s     |

The 30-second floor is the QE's indexing pipeline latency and cannot be reduced.

## Cost comparison

Batch ingestion is not cheaper than streaming on a per-event basis; both are
billed by uncompressed bytes ingested. However, batch ingestion generates fewer
API calls, which reduces the chance of hitting per-second rate limits and
simplifies retry logic.

## Historical data load

When loading historical data, use the `--file` flag with `nbx ingest`. For very
large historical loads (hundreds of GB), contact Cirrus Systems support to
arrange a bulk import that bypasses IGW rate limits temporarily.
