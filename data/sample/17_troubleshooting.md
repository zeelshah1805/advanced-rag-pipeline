# Nimbus Troubleshooting Guide

## Ingestion issues

### HTTP 429 — Rate limit exceeded
Your ingest rate is above the plan limit. The `Retry-After` header gives the
number of seconds to wait. Implement truncated exponential backoff (start 1s,
double, cap at 60s). The `nimbus-sdk` and `nbx` do this automatically.

If you consistently hit 429, either reduce your send rate, batch events more
aggressively, or upgrade to a higher plan.

### HTTP 422 — Validation error
You have strict-mode schema validation enabled and an event failed it. The
response body contains a `violations` array with field-level details. Either
fix the producer or update the schema in the Schema Registry.

### Events not appearing in queries
Check the following in order:
1. Confirm the ingest call returned HTTP 200. If you got 429 or 422, events
   were not accepted.
2. Allow up to 30 seconds for events to be visible in the Query Engine after
   a successful ingest.
3. Verify you are querying the correct dataset and region.
4. Check that your `_received_at` filter covers the expected time window.

### `nbx ingest` exits with "payload too large"
A single file sent to `nbx ingest` is split automatically at 10,000 events or
10 MB. This error means a **single line** in your NDJSON file exceeds 64 KB.
Reduce the event size; store large blobs externally.

## Query issues

### Query returns no results but data was ingested
The most common cause is an off-by-one in the time filter. Always filter on
`_received_at`, not a client-side timestamp field, because `_received_at` is
set by the IGW and is guaranteed to be indexed.

### Query is slower than expected
- Use `--dry-run` to see how many bytes will be scanned.
- Add a `WHERE _received_at BETWEEN ... AND ...` clause to prune partitions.
- Consider a materialized view if the same aggregation runs frequently.
- Avoid `SELECT *`; project only needed columns.

### `ERROR: Concurrency limit reached`
You have hit the concurrent-query limit for your plan (2 for Free, 20 for
Scale). Queries are queued and time out after 5 minutes. Reduce parallelism or
upgrade your plan.

## Authentication issues

### HTTP 401 — Unauthorized
- Verify `NBX_API_KEY` is set correctly in the environment.
- Check that the key has not expired and has not been rotated without updating
  the deployment.
- Confirm the key was created for the same region as the endpoint you are
  calling.

### HTTP 403 — Forbidden
The key is valid but does not have the required role. For example, changing RPL
settings requires the `admin` role; a `writer` key will receive 403.

## CLI issues

### `nbx: command not found`
Install `nbx` or add it to your `PATH`. On macOS/Linux:
```bash
curl -fsSL https://get.nimbus.io/nbx | bash
```
On Windows, use the MSI installer from the Nimbus console downloads page.

### `nbx auth login` fails with "invalid region in key"
The API key prefix encodes the region. Ensure you are logging in with a key
created for the intended region. Keys from `eu-west-1` will not authenticate
against `us-east-1` endpoints.
