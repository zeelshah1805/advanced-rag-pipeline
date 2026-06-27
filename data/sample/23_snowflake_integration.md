# Nimbus Snowflake Integration

Nimbus can sync data to Snowflake using the Nimbus Snowflake Connector. This
allows you to join Nimbus event data with your existing Snowflake data warehouse
tables for BI and analytics workloads. The connector is available on Scale and
Enterprise plans.

## How it works

The connector runs as a managed service inside Nimbus. It periodically queries
Nimbus for new events since the last sync, converts them to Parquet, and loads
them into a Snowflake table using the Snowflake `COPY INTO` command. No Nimbus
data ever transits through your infrastructure — the connector runs inside the
Nimbus control plane.

## Prerequisites

- A Snowflake account with a database and schema where the connector can create
  tables.
- A Snowflake user with `USAGE` on the warehouse, `CREATE TABLE` on the schema,
  and `COPY FILES` privilege.
- A Snowflake storage integration that allows Nimbus's S3 staging bucket.

## Configuration

Set up via the console under **Dataset → Integrations → Snowflake**:

1. Enter your Snowflake account identifier (e.g. `xy12345.us-east-1`).
2. Enter the database, schema, and warehouse name.
3. Paste the Snowflake user credentials (username + private key; password auth
   is not supported).
4. Set the sync interval (minimum 5 minutes).
5. Nimbus will test the connection and create the target table on first sync.

## Target table schema

Nimbus creates the target table with columns derived from the dataset's inferred
schema. Reserved Nimbus fields (`_received_at`, `_ingest_id`, `_dataset`) are
always included. The table is append-only; Nimbus does not update or delete rows
in Snowflake even if you run a purge in Nimbus.

## Sync behaviour

- Each sync appends rows for events ingested since the last successful sync.
- Sync uses `_received_at` to determine which events are new.
- If a sync fails, it retries from the last checkpoint; no events are skipped
  or duplicated.
- Schema evolution: new fields in Nimbus are automatically added as new columns
  in Snowflake (`ALTER TABLE ADD COLUMN`). Removed fields leave the old column
  in place with `NULL` values for new rows.

## Latency

Snowflake data lags Nimbus by at most one sync interval plus a few seconds for
the Snowflake `COPY INTO` to complete. At a 5-minute interval, Snowflake data
is typically 5–10 minutes behind live Nimbus data.

## Cost

The Snowflake connector is included in the Scale plan at no extra charge.
Snowflake compute costs (virtual warehouse usage during `COPY INTO`) are billed
to your Snowflake account. Nimbus uses the smallest compatible warehouse size
by default; configure `warehouse_size` in the connector settings to override.
