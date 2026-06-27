# Migrating to Nimbus from Other Platforms

This guide covers migrating event data and pipelines to Nimbus from common
alternatives: Elasticsearch, BigQuery, Splunk, and custom PostgreSQL setups.

## From Elasticsearch

**Data migration:**
Export your Elasticsearch indices to NDJSON using `elasticdump` or the
Elasticsearch Scroll API. Each document becomes one Nimbus event. Map the
`@timestamp` field to a field ending in `_at` so Nimbus auto-indexes it as a
timestamp.

```bash
elasticdump --input=http://localhost:9200/my-index \
            --output=events.ndjson \
            --type=data
nbx ingest my-nimbus-dataset --file events.ndjson
```

**Query translation:**
Elasticsearch Query DSL is not compatible with Nimbus SQL. Rewrite queries
as SQL. Elasticsearch's `terms` aggregation maps to `GROUP BY`; `date_histogram`
maps to `TIMEBUCKET`.

**Ingest pipeline:**
Replace Logstash or Beats with the Nimbus Kafka Connector (if Kafka is in your
stack) or the Python/Node.js SDK.

## From BigQuery

**Data migration:**
Export BigQuery tables to GCS as Parquet, then import to Nimbus via the
S3-compatible GCS endpoint. Alternatively, export to NDJSON and use `nbx ingest`.

**Query translation:**
Nimbus SQL is close to BigQuery Standard SQL. Key differences:
- BigQuery's `TIMESTAMP_TRUNC(ts, HOUR)` → Nimbus `TIMEBUCKET(_received_at, '1h')`.
- BigQuery table references use backticks; Nimbus uses plain identifiers.
- BigQuery `APPROX_COUNT_DISTINCT` → Nimbus `APPROX_COUNT_DISTINCT` (same name).

**Ingest pipeline:**
Replace BigQuery Streaming API calls with Nimbus IGW calls. The request
structure differs but the concept (HTTP POST of JSON events) is the same.

## From Splunk

**Data migration:**
Use the Splunk `export` command to dump events as JSON. The Splunk `_time`
field maps to Nimbus `_received_at` (rename during migration).

```splunk
| search index=main earliest=-90d | table _time, host, source, _raw
| outputcsv events.csv
```

Convert the CSV to NDJSON with `jq` or a Python script before ingesting.

**Query translation:**
Splunk's SPL (Search Processing Language) does not translate directly to SQL.
Rethink queries from scratch using Nimbus SQL. Common mappings:
- `stats count by host` → `SELECT host, COUNT(*) FROM dataset GROUP BY host`.
- `timechart span=1h count` → `SELECT TIMEBUCKET(_received_at,'1h'), COUNT(*) ... GROUP BY 1`.

## From custom PostgreSQL

**Data migration:**
Use `COPY TO` to export PostgreSQL tables as CSV, convert to NDJSON, and ingest.
Ensure timestamp columns are exported as ISO-8601 UTC strings.

**Query translation:**
Nimbus SQL is largely compatible with PostgreSQL SQL. The main gaps:
- No `UPDATE` or `DELETE` (Nimbus is append-only; use RPL purge for deletions).
- No `JOIN` across datasets (each query targets one dataset).
- `NOW()` and `INTERVAL` syntax is supported and behaves identically.

**Ingest pipeline:**
Replace `INSERT` statements with Nimbus IGW calls or use the Python SDK.
For CDC (change data capture) workloads, use Debezium to capture PostgreSQL
changes and route them to Nimbus via the Kafka Connector.
