# Nimbus Performance Tuning

## Ingestion throughput

### Batch size
The single biggest lever is batch size. Small batches (1–10 events per call)
waste HTTP overhead. Aim for 1,000–5,000 events per call. The `StreamingIngestor`
defaults to 5,000 events or 2 seconds, whichever comes first.

### Parallelism
The IGW is stateless and horizontally scaled. You can safely open multiple
concurrent ingest connections. For very high throughput (>50,000 eps), use
4–8 parallel writers, each sending batches of 5,000 events. Limit per-worker
rate to avoid a single writer triggering 429s.

### Compression
Enable gzip compression (`Content-Encoding: gzip`) for payloads that compress
well (JSON typically achieves 5:1). This reduces bandwidth and can cut ingest
latency by 20–40% on high-latency networks.

### Protocol choice
gRPC outperforms HTTP/1.1 at high concurrency because it multiplexes requests
over a single TCP connection. Prefer gRPC if your producer supports it and
you are sending more than 5,000 eps.

## Query performance

### Partition pruning
Always include a `WHERE _received_at BETWEEN ... AND ...` clause. The QE uses
`_received_at` as the primary partition key and skips entire hourly partitions
outside the range. Without this filter, every query scans all partitions.

### Column projection
`SELECT *` forces the QE to decode all columns from the columnar store. Project
only the columns your query needs. On wide datasets (50+ columns), this can
reduce scan time and cost by 10×.

### APPROX_COUNT_DISTINCT vs COUNT(DISTINCT)
`APPROX_COUNT_DISTINCT` uses HyperLogLog and is 10–100× faster than exact
`COUNT(DISTINCT ...)` for high-cardinality columns. The error is ≤2%; use
the exact version only when you need an exact count.

### MATCH vs LIKE
`MATCH(column, pattern)` uses the inverted index and is orders of magnitude
faster than `LIKE '%pattern%'` for full-text search on large datasets. Use
`LIKE` only for prefix matches (`LIKE 'prefix%'`) which are also index-friendly.

### Materialized views for repeated aggregations
If the same `GROUP BY` aggregation runs more than a few times per hour, create
a materialized view. The view's cached result is scanned instead of the full
dataset, reducing both latency and cost.

## Storage efficiency

### Retention tuning
Set retention to the minimum your use case requires. Shorter retention means
less stored data, lower storage costs, and faster full-dataset scans.

### Event size
Keep events small. Each KB of event payload adds to ingestion cost and storage.
Avoid embedding large blobs (images, documents) in events; store them in S3
and include only the reference URL in Nimbus.

### Field naming
Use short, consistent field names. Field names are stored with each column's
metadata and contribute to per-event overhead at small event sizes.

## Benchmarking your setup

Use `nbx query --dry-run` to estimate scan bytes before committing to a query
design. Compare estimated bytes before and after adding a time filter or
projecting fewer columns to quantify the optimisation impact.

For ingest benchmarking, the Python SDK ships a `benchmark` utility:
```bash
python -m nimbus.benchmark --dataset my-dataset --eps 10000 --duration 60
```
This generates synthetic events and reports achieved throughput and 429 rate.
