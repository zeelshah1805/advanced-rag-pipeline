# nbx Command-Line Reference

`nbx` is the official Nimbus command-line tool. It reads its API key from the
`NBX_API_KEY` environment variable or from `~/.nbx/credentials`.

## nbx auth login

Stores an API key locally. Usage: `nbx auth login --key <API_KEY>`. The key is
validated against the region encoded in the key prefix.

## nbx dataset create

Creates a dataset. Usage: `nbx dataset create <name> --retention <days>`. The
`--retention` flag accepts a value between 1 and the plan maximum; omitting it
applies the 30-day default. A dataset's region is inherited from the API key and
cannot be changed afterward.

## nbx ingest

Sends events to the Ingestion Gateway. Usage: `nbx ingest <dataset> --file
<path>`. The file must be newline-delimited JSON. If the ingestion rate exceeds
the plan limit, the gateway returns HTTP 429 and `nbx` retries with exponential
backoff up to five times.

## nbx query

Runs a query on the Query Engine. Usage: `nbx query "<SQL>"`. Queries are billed
by compute time. The `--dry-run` flag estimates the scanned bytes without
executing and without incurring query charges.

## nbx purge

Triggers a GDPR hard delete via the RPL purge API. Requires the `admin` role.
Usage: `nbx purge <dataset> --where "<filter>"`. The deletion completes within
72 hours.
