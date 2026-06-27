# Nimbus Pricing FAQ

## Do I pay for events that are rate-limited or rejected?

No. You are billed only for events that are successfully accepted by the
Ingestion Gateway (HTTP 200). Events returning HTTP 429 (rate limit) or
HTTP 422 (schema validation failure) are not billed.

## How is storage billed for datasets with short retention?

Storage is billed on the compressed bytes stored at any given moment. If a
dataset has 30-day retention, events older than 30 days are deleted by the RPL
and stop accruing storage charges within 72 hours of deletion.

## Is there a minimum spend on the Scale plan?

No. The Scale plan is pure pay-as-you-go with no monthly minimum. If you ingest
nothing in a month, your bill is $0. You only pay for what you use.

## How are materialized view refreshes billed?

Refreshing a materialized view consumes Query Engine compute against the source
dataset (billed by bytes scanned). The view itself occupies storage (billed as
stored bytes). Querying the view is billed only against the view's stored size,
which is typically much smaller than the source dataset.

## Can I set a spending cap?

Yes. Set a monthly budget alert in **Billing → Budget Alerts**. When the
projected spend exceeds the threshold, Nimbus sends an email alert. You can
also configure a hard cap that suspends ingestion (but not queries) when the
cap is reached. Hard caps are available on the Scale plan and above.

## What happens if I exceed the Free plan storage limit?

When a Free plan account's stored data reaches 5 GB, ingestion is blocked
(HTTP 429 with a `storage_cap_exceeded` error code). Existing data remains
queryable. To resume ingestion, either delete datasets to free storage or
upgrade to the Scale plan.

## Are there charges for cross-region data transfer?

Cross-region replication (Enterprise only) incurs data transfer charges at the
cloud provider's inter-region rate. S3 export to a bucket in the same region
as the Nimbus dataset incurs no transfer charge; cross-region S3 exports do.

## Is the Query Engine free on the Free plan?

The Free plan has access to the Query Engine but the concurrent-query limit is
2 and materialized views are not available. Query compute is billed the same
way on all plans (per TB scanned).

## How do I estimate my monthly bill?

Use the pricing calculator at cirrus.io/pricing. Key inputs: events per day,
average event size (KB), number of active datasets and their retention periods,
and estimated query volume (TB scanned per month).

## Does Nimbus offer startup or non-profit discounts?

Yes. Startups that raised less than $5M and non-profit organisations can apply
for a 30% discount on Scale plan usage. Apply at cirrus.io/startups or
cirrus.io/nonprofits. Discounts do not stack with prepaid credit discounts.
