# Nimbus Plans and Limits

Nimbus is sold in three plans: Free, Scale, and Enterprise. Pricing is based on
a combination of ingested volume, stored volume, and query compute.

## Free plan

The Free plan is intended for evaluation. It allows up to 5 GB of stored data
and a maximum ingestion rate of 100 events per second through the Ingestion
Gateway. Data retention on the Free plan is fixed at 30 days and cannot be
changed. The Free plan does not include access to the Query Engine's
materialized views and has no service-level agreement.

## Scale plan

The Scale plan is the default choice for production workloads. It raises the
ingestion limit to 10,000 events per second and allows stored data up to
2 TB. On the Scale plan, retention can be configured per dataset up to a
maximum of 365 days. The Scale plan includes a 99.9% uptime SLA and email
support with a 24-hour response target.

## Enterprise plan

The Enterprise plan removes fixed storage and ingestion caps; limits are set by
contract. Retention can be unlimited. Enterprise includes a 99.99% uptime SLA,
a dedicated support channel, and single-sign-on (SSO) via SAML. Only the
Enterprise plan offers private network peering (VPC peering).

## Summary of key differences

- Ingestion cap: Free 100 eps, Scale 10,000 eps, Enterprise by contract.
- Max retention: Free 30 days, Scale 365 days, Enterprise unlimited.
- SLA: Free none, Scale 99.9%, Enterprise 99.99%.
- SSO and VPC peering are Enterprise-only.
