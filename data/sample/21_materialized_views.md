# Nimbus Materialized Views

Materialized views pre-compute and cache the results of expensive queries so
subsequent reads scan only the cached output rather than the full dataset.
They are available on the Scale and Enterprise plans.

## When to use a materialized view

A materialized view is appropriate when:
- The same aggregation query runs frequently (e.g. hourly dashboards).
- The underlying dataset is large and the query scans many partitions.
- Near-real-time freshness (within minutes) is acceptable.

Materialized views are **not** appropriate for ad-hoc exploratory queries or
for queries that require exactly up-to-the-second data.

## Creating a materialized view

```bash
POST /v1/datasets/{source_dataset}/views
{
  "name": "hourly_clicks",
  "sql": "SELECT TIMEBUCKET(_received_at, '1h') AS hour, COUNT(*) AS clicks FROM clicks GROUP BY hour",
  "refresh_interval_minutes": 5
}
```

Or via `nbx`:
```bash
nbx view create hourly_clicks \
  --dataset clicks \
  --sql "SELECT TIMEBUCKET(_received_at, '1h') AS hour, COUNT(*) AS clicks FROM clicks GROUP BY hour" \
  --refresh 5m
```

The minimum refresh interval is 1 minute. The view is computed in full on the
first refresh, then incrementally updated on subsequent refreshes.

## Querying a materialized view

Query a view exactly like a dataset:
```bash
nbx query "SELECT * FROM hourly_clicks WHERE hour > '2024-01-01'"
```

The QE routes the query to the view's cached output. Scanned bytes reflect
the view's stored size, which is typically orders of magnitude smaller than
the source dataset.

## View staleness

A view is at most `refresh_interval_minutes` stale plus the time of the last
refresh cycle (typically under 30 seconds). The view API exposes
`last_refreshed_at` and `next_refresh_at` fields.

If a refresh fails, the view continues to serve the last successful result.
Failed refreshes generate an alert if an alert rule is configured on the
`view.refresh_failed` metric.

## Limitations

- A materialized view cannot reference another materialized view.
- The source SQL must be a `SELECT` with `GROUP BY`; `JOIN` across datasets is
  not supported in views.
- Views are deleted if the source dataset is deleted.
- Maximum 50 materialized views per account on Scale; unlimited on Enterprise.

## Cost

Refreshing a materialized view consumes QE compute (billed by bytes scanned
from the source dataset). Once stored, querying the view is billed only against
the view's small stored size. For frequently-queried aggregations, views
typically reduce query costs by 10–100×.
