# Nimbus Query Engine (QE) — Deep Dive

The Query Engine executes analytical queries over stored Nimbus data. It was
rewritten as a columnar, vectorized engine in version 2.0 (September 2023),
replacing the row-based engine from the 1.x line. Analytical queries are
typically 4× faster on the new engine.

## SQL dialect

The QE accepts ANSI SQL with the following Nimbus-specific extensions:

- `TIMEBUCKET(<column>, <interval>)` — truncates a timestamp column to the
  given interval (e.g. `'1h'`, `'15m'`, `'1d'`). Used for time-series
  aggregation.
- `APPROX_COUNT_DISTINCT(<column>)` — HyperLogLog-based cardinality estimation;
  much faster than `COUNT(DISTINCT ...)` on large datasets, with ≤2% error.
- `MATCH(<column>, <pattern>)` — full-text search within a string column using
  the Nimbus inverted index. Faster than `LIKE '%...%'` for large datasets.

Standard SQL window functions (`ROW_NUMBER`, `RANK`, `LAG`, `LEAD`, `SUM OVER`,
etc.) are fully supported.

## Billing

Queries are billed by **bytes scanned**, not by rows or query count. The rate
is shown in the billing section of the console. Using `nbx query --dry-run`
estimates scanned bytes before executing without incurring charges.

To minimize scan costs:
- Filter on the `_received_at` column first; the QE uses it as the primary
  partition key and will skip partitions outside the filter range.
- Project only the columns you need (`SELECT a, b` rather than `SELECT *`).
- Use materialized views (Scale and Enterprise plans) to pre-aggregate expensive
  queries.

## Materialized views

A materialized view is a pre-computed query result that the QE refreshes
incrementally as new data arrives. They are available on the Scale and Enterprise
plans. Querying a materialized view scans only the view's stored output, not the
underlying dataset, which can reduce costs by 10–100×.

Create a materialized view via the console or REST API. You must specify a
refresh interval (minimum 1 minute). Materialized views cannot reference other
materialized views.

## Concurrency and quotas

Each plan has a concurrent-query limit:

| Plan       | Concurrent queries |
|------------|--------------------|
| Free       | 2                  |
| Scale      | 20                 |
| Enterprise | Contractual        |

Queries that exceed the concurrency limit are queued, not rejected. Queued
queries time out after 5 minutes if no slot becomes available.

## Query result format

Results are returned as NDJSON by default. Pass `Accept: text/csv` to receive
CSV. Large result sets are paginated; the response includes a `next_cursor`
field when more pages exist. Pass `cursor=<value>` to fetch the next page.

## `--dry-run` flag

`nbx query --dry-run "<SQL>"` sends the query plan to the QE without executing
it. The response contains the estimated bytes to be scanned and the partition
ranges that would be read. No query charges are incurred.
