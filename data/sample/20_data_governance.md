# Nimbus Data Governance

Data governance in Nimbus covers data lineage, classification, retention
enforcement, and deletion compliance. These features are primarily relevant for
organisations with GDPR, CCPA, or internal data-management obligations.

## Data classification

Nimbus supports tagging datasets with classification labels to indicate
sensitivity. Labels are free-form strings (e.g. `pii`, `financial`,
`internal-only`). Labels are visible in the dataset list and can be used
to filter in the console and REST API.

Labels are metadata only — they do not change storage or access behaviour.
Enforce access restrictions through RBAC roles and API key scoping.

## Retention enforcement

The Retention Policy Layer (RPL) automatically deletes events older than the
configured retention period. Deletion runs daily and removes entire storage
partitions; it is not event-level deletion. There is no way to recover events
deleted by the RPL.

Retention is set per dataset:
```bash
nbx dataset create my-dataset --retention 180
```

Or updated after creation (requires `admin` role):
```bash
PUT /v1/datasets/my-dataset
{ "retention_days": 90 }
```

Reducing retention takes effect at the next daily RPL run. Events older than
the new retention period are deleted at that time.

## GDPR right to erasure

To fulfil a GDPR right-to-erasure (right to be forgotten) request:

1. Use the RPL purge API to delete all events matching the subject's identifier:
   ```bash
   nbx purge my-dataset --where "user_id = '12345'"
   ```
2. Purge completes within 72 hours and applies to all storage replicas and
   cross-region replicas.
3. The purge operation is recorded in the audit log with the executing user,
   the filter expression, and the timestamp.

Purge does not retroactively remove the subject's data from S3 exports that
have already been written. You are responsible for handling erasure in your
downstream systems.

## Data lineage

Nimbus records dataset-level lineage automatically: which API key ingested data,
when, and from which source IP. Lineage is visible in the console under
**Dataset → Lineage** and exportable via the audit log API.

Column-level lineage (tracking which source field maps to which QE column) is
not currently supported.

## Audit log for compliance

The immutable audit log records all administrative actions: dataset creation and
deletion, RPL changes, purge operations, API key creation and rotation, and
user login/logout (for SSO accounts). Audit log entries cannot be deleted.

Audit log retention:
- Scale plan: 90 days.
- Enterprise plan: 1 year.
- Free plan: no audit log.

To export audit logs for external SIEM systems, use the audit log export API
(`GET /v1/audit-log/export`) or configure a webhook alert on `audit.action`
events.

## Data minimisation

Nimbus recommends ingesting only the fields your queries actually need. Avoid
ingesting raw PII (names, email addresses, phone numbers) unless necessary;
use pseudonymous identifiers where possible. The Schema Registry's strict mode
can be used to reject payloads containing disallowed field names.
