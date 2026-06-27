# Nimbus S3 Export

Nimbus can export dataset data to Amazon S3 (or any S3-compatible object store)
on a scheduled or on-demand basis. S3 export is available on the Scale and
Enterprise plans.

## Setting up an export destination

1. In the console, go to **Dataset → Exports → Add Destination**.
2. Enter the S3 bucket name, prefix, and the ARN of an IAM role that grants
   Nimbus `s3:PutObject` permission on the bucket.
3. Nimbus will perform a test write to verify permissions before saving.

The IAM role must include the following trust policy to allow Nimbus to assume it:

```json
{
  "Effect": "Allow",
  "Principal": { "AWS": "arn:aws:iam::123456789012:root" },
  "Action": "sts:AssumeRole",
  "Condition": {
    "StringEquals": { "sts:ExternalId": "<your-nimbus-account-id>" }
  }
}
```

The external ID is shown in the console during destination setup and must match
exactly.

## Scheduled exports

Scheduled exports run at a configurable interval (minimum 1 hour). Each run
exports all events ingested since the last successful run. Files are written in
Parquet format by default; NDJSON is also available.

File naming convention:
```
<prefix>/<dataset>/<year>/<month>/<day>/<timestamp>-<shard>.parquet
```

## On-demand exports

Trigger an export for a specific time range via the REST API:

```bash
POST /v1/datasets/{dataset}/exports
{
  "destination": "my-s3-dest",
  "from": "2024-01-01T00:00:00Z",
  "to":   "2024-01-31T23:59:59Z",
  "format": "parquet"
}
```

The response includes an `export_id`. Poll `GET /v1/exports/{export_id}` to
check status. Large exports may take several minutes.

## Encryption

Exported files use SSE-S3 encryption by default. To use SSE-KMS, specify your
KMS key ARN in the destination configuration.

## Partition columns

Parquet exports are partitioned by `_year`, `_month`, `_day`, and `_hour`
derived from the `_received_at` field. This allows query tools such as AWS
Athena to prune partitions efficiently.

## Supported object stores

In addition to Amazon S3, Nimbus supports:
- **Google Cloud Storage** — uses a GCS HMAC key instead of an IAM role.
- **Azure Blob Storage** — uses a Shared Access Signature (SAS) token.
- **MinIO** — set a custom endpoint URL in the destination configuration.

## Cost

S3 export does not consume Query Engine compute credits. You pay only for
Nimbus storage (the data remains in Nimbus after export) and the S3 storage
costs in your own account. PUT request charges to S3 are your responsibility.
