# Nimbus Alerts and Monitoring

Nimbus exposes platform health and dataset-level metrics through a built-in
monitoring subsystem. Metrics are visible in the console and can trigger alerts.

## Available metrics

### Dataset metrics (per dataset)
- `ingest.events_per_second` — smoothed 1-minute average ingestion rate.
- `ingest.rejected_per_second` — events rejected by strict-mode schema
  validation.
- `ingest.rate_limited_per_second` — requests returning HTTP 429.
- `storage.bytes_stored` — current compressed storage consumed.
- `storage.retention_days` — configured retention for the dataset.
- `query.scanned_bytes_per_hour` — query scan volume billed in the last hour.

### Account metrics
- `account.datasets_count` — total number of datasets.
- `account.total_storage_bytes` — aggregate storage across all datasets.

## Alert rules

Alert rules evaluate a metric against a threshold and send notifications when
the threshold is crossed. Rules are created in the console under
**Monitoring → Alert Rules** or via the REST API (`POST /v1/alerts`).

Each rule specifies:
- **Metric** — one of the metrics above.
- **Condition** — `above`, `below`, or `equals`.
- **Threshold** — numeric value.
- **Duration** — how long the condition must hold before firing (1–60 minutes).
- **Notification channels** — where to send the alert.

## Notification channels

| Channel     | Plans          | Notes                                       |
|-------------|----------------|---------------------------------------------|
| Email       | All plans      | Up to 5 addresses per alert rule.           |
| Webhook     | Scale, Enterprise | POST to your endpoint with JSON payload. |
| PagerDuty   | Enterprise     | Requires PagerDuty integration key.         |
| Slack       | Scale, Enterprise | Requires Slack OAuth app installation.   |

Webhook payloads include: `alert_id`, `rule_name`, `metric`, `value`,
`threshold`, `fired_at` (UTC ISO-8601), and `dataset` (if applicable).

## Metric retention

Raw metric data is retained for 30 days. Aggregated hourly rollups are retained
for 13 months. Alert history is retained for 90 days.

## Pre-built dashboards

The console ships four pre-built dashboards: **Ingestion Health**,
**Query Performance**, **Storage Utilisation**, and **Rate Limit Events**.
Custom dashboards are available on the Scale and Enterprise plans.

## Recommended alert rules

1. `ingest.rate_limited_per_second > 0 for 5 minutes` — warns that clients are
   being throttled and may be dropping data.
2. `storage.bytes_stored > 80% of plan limit for 15 minutes` — warns before
   hitting the hard storage cap.
3. `ingest.rejected_per_second > 10 for 2 minutes` — indicates a producer is
   sending malformed events in strict mode.
