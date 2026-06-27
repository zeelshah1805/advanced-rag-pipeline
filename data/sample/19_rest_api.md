# Nimbus REST API Reference

The Nimbus REST API is versioned. The current version is `v1`. All endpoints
are under `https://api.<region>.nimbus.io/v1/`.

## Authentication

Every request must include an `Authorization: Bearer <API_KEY>` header. Requests
without a valid key return HTTP 401. Requests with a key that lacks the required
role return HTTP 403.

## Common response codes

| Code | Meaning                                                    |
|------|------------------------------------------------------------|
| 200  | Success.                                                   |
| 201  | Resource created.                                          |
| 400  | Malformed request body.                                    |
| 401  | Missing or invalid API key.                                |
| 403  | Key valid but insufficient role.                           |
| 404  | Resource not found.                                        |
| 409  | Conflict (e.g. dataset name already exists).               |
| 422  | Schema validation failure (strict mode).                   |
| 429  | Rate limit exceeded; see `Retry-After` header.             |
| 5xx  | Server error; safe to retry with backoff.                  |

## Datasets

### `GET /v1/datasets`
List all datasets in the region. Requires `reader` role.

Response: `{ "datasets": [ { "name": "...", "retention_days": 30, "created_at": "..." } ] }`

### `POST /v1/datasets`
Create a dataset. Requires `admin` role.

Request body: `{ "name": "my-dataset", "retention_days": 90, "strict_schema": false }`

### `DELETE /v1/datasets/{name}`
Schedule a dataset for deletion (72-hour grace period). Requires `admin` role.

## Ingestion

### `POST /v1/ingest/{dataset}`
Ingest events. Requires `writer` or `admin` role. Body must be NDJSON with
`Content-Type: application/x-ndjson`. Returns `{ "accepted": N, "rejected": M }`.

## Queries

### `POST /v1/query`
Execute a SQL query. Requires `reader` role.

Request: `{ "sql": "SELECT ...", "dataset": "my-dataset" }`
Response: `{ "rows": [...], "scanned_bytes": N, "next_cursor": "..." }`

### `POST /v1/query/dry-run`
Estimate bytes scanned without executing. Returns `{ "estimated_bytes": N }`.

## Exports

### `POST /v1/datasets/{dataset}/exports`
Trigger an on-demand S3 export. Requires `admin` role.

### `GET /v1/exports/{export_id}`
Poll export status. Returns `{ "status": "running|completed|failed", "file_count": N }`.

## Alerts

### `GET /v1/alerts`
List all alert rules. Requires `reader` role.

### `POST /v1/alerts`
Create an alert rule. Requires `admin` role.

### `DELETE /v1/alerts/{alert_id}`
Delete an alert rule. Requires `admin` role.

## Pagination

List endpoints return at most 100 items. Pass `?cursor=<next_cursor>` from the
previous response to get the next page. When `next_cursor` is absent, the last
page has been reached.

## Rate limits on the API itself

The REST API (non-ingest endpoints) is rate-limited at 120 requests per minute
per API key. Exceeding this returns HTTP 429 with a `Retry-After` header.
Ingest rate limits are governed separately by the plan limits on the IGW.
