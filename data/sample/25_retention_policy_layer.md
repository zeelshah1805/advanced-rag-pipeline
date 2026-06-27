# Nimbus Retention Policy Layer (RPL)

The Retention Policy Layer is the subsystem responsible for determining how long
data is kept and for enforcing deletions. It is the component most often
misconfigured by new users, so this document explains it in detail.

## How RPL works

The RPL evaluates every dataset once per day against its configured retention
period. When it finds storage partitions containing only events older than the
retention threshold, it deletes those partitions atomically. Deletion is
permanent and cannot be undone.

RPL deletions happen at **partition granularity**, not event granularity. A
partition holds events for a 1-hour window. If even one event in a partition
is within the retention window, the entire partition is retained. This means
actual data lifetime can be up to `retention_days + 23 hours`.

## Configuring retention

Retention is set per dataset at creation time or updated afterward. The `admin`
role is required to change retention.

```bash
# at creation
nbx dataset create my-dataset --retention 90

# update existing dataset
nbx dataset update my-dataset --retention 180
```

Via the REST API:
```bash
PUT /v1/datasets/my-dataset
{ "retention_days": 180 }
```

Changes take effect at the next daily RPL run. **Reducing** retention deletes
all partitions outside the new window on the next run. **Increasing** retention
does not restore already-deleted data.

## Plan retention limits

| Plan       | Minimum retention | Maximum retention |
|------------|-------------------|-------------------|
| Free       | 30 days (fixed)   | 30 days (fixed)   |
| Scale      | 1 day             | 365 days          |
| Enterprise | 1 day             | Unlimited         |

The Free plan retention is fixed at 30 days and cannot be changed by any role.
Only admins can change retention on Scale and Enterprise.

## Purge API (event-level deletion)

For GDPR and right-to-erasure use cases, the RPL exposes a purge API that
deletes individual events matching a filter expression:

```bash
nbx purge my-dataset --where "user_id = '12345'"
```

Purges complete within 72 hours and are recorded in the immutable audit log.
Unlike partition-level retention, purges target individual events. Purges
require the `admin` role.

## Interaction with S3 export

The RPL deletes data from Nimbus storage only. Events already exported to S3
via the S3 Export feature are **not** deleted by the RPL or by purges. You are
responsible for managing lifecycle rules in your S3 bucket independently.

## Audit trail for RPL changes

Every change to a dataset's retention period is recorded in the audit log with
the old value, the new value, the admin user or API key that made the change,
and the timestamp. This provides a full history for compliance reviews.
