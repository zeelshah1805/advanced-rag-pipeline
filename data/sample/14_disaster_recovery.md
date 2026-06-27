# Nimbus Disaster Recovery and Backups

Nimbus is designed for high durability. All data is stored with 11-nines
(99.999999999%) durability by replicating across three availability zones within
the dataset's region.

## Automatic snapshots

Nimbus takes automatic snapshots of each dataset every 6 hours. Snapshots are
stored in a separate fault domain from live data and can be used to restore a
dataset to any snapshot point in the past 7 days.

Snapshot retention:

| Plan       | Snapshot window |
|------------|-----------------|
| Free       | 24 hours (4 snapshots) |
| Scale      | 7 days          |
| Enterprise | 30 days         |

## Restoring from a snapshot

Restore is available from the console under **Dataset → Snapshots** or via the
REST API:

```bash
POST /v1/datasets/{dataset}/restore
{
  "snapshot_id": "snap_20240115_060000",
  "target_dataset": "my-dataset-restored"
}
```

Restoration creates a new dataset; it does not overwrite the live dataset.
After verifying the restored data, you can delete the original and rename the
restored dataset. Restoration typically completes within 15 minutes for datasets
up to 100 GB; larger datasets may take longer.

## Cross-region replication (Enterprise)

Enterprise customers can enable cross-region replication to keep a live replica
of a dataset in a second region. The replica has a replication lag of typically
under 60 seconds. Cross-region replication is read-only on the replica side;
writes must go to the primary region.

To enable, contact your Cirrus Systems account manager. Cross-region data
transfer costs apply.

## Regional failover

In the event of a regional outage, Nimbus automatically fails reads over to the
cross-region replica for Enterprise customers. Writes are held in a durable
queue and replayed when the primary region recovers. RTO (Recovery Time
Objective) for Enterprise is under 15 minutes. RPO (Recovery Point Objective)
is under 60 seconds, matching the replication lag.

Scale and Free plans do not include automated failover. In a regional outage,
the platform is unavailable until the affected region recovers; no data is lost
because all writes are synchronously committed to at least two AZs before
acknowledgement.

## Data deletion and purge

Deleting a dataset schedules it for permanent removal within 72 hours. During
this window, deletion can be cancelled from the console. After 72 hours, data
is cryptographically erased and cannot be recovered, including from snapshots.

The RPL purge API (`nbx purge`) performs a hard delete of matching events within
72 hours. Purges cannot be undone and are reflected in audit logs.
