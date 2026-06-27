# Nimbus Billing and Invoicing

Nimbus bills on three independent dimensions: **ingested volume**,
**stored volume**, and **query compute**. These are metered separately and
appear as distinct line items on your invoice.

## Ingested volume

Charged per GB of raw (uncompressed) event data accepted by the Ingestion
Gateway. Events that are rejected (HTTP 422 schema violation) or rate-limited
(HTTP 429) are not billed. Nimbus applies roughly 4:1 compression before
writing to storage, but billing is based on uncompressed ingest bytes, not
stored bytes.

## Stored volume

Charged per GB per month of compressed data stored across all datasets. The
meter is sampled hourly and averaged over the billing month. Deleted or
purged data stops accruing storage charges within 72 hours.

## Query compute

Charged per TB of data scanned by the Query Engine. Querying a materialized
view is billed against the view's stored size, not the underlying dataset.
`nbx query --dry-run` estimates scan volume at no cost.

## Plan minimums and caps

| Plan       | Monthly minimum | Storage cap | Ingestion cap  |
|------------|-----------------|-------------|----------------|
| Free       | $0              | 5 GB        | 100 eps        |
| Scale      | $0 (pay-as-you-go) | 2 TB     | 10,000 eps     |
| Enterprise | Contractual     | Contractual | Contractual    |

The Free plan has no monthly charge; usage beyond the 5 GB storage cap is
blocked (not billed). Scale and Enterprise overages beyond contract are billed
at list rates.

## Billing cycle

Invoices are generated on the 1st of each month for the prior month's usage.
Payment is due within 30 days. Credit card payment is handled via Stripe; wire
transfer is available for Enterprise accounts.

## Usage dashboard

Real-time usage is visible in the console under **Billing → Usage**. The
dashboard shows current-month spend broken down by dimension and by dataset.
Cost anomaly alerts can be configured to notify when daily spend exceeds a
threshold.

## Invoices

Past invoices are available for download as PDF under **Billing → Invoices**.
Invoices include an itemized breakdown of ingest, storage, and query compute
by dataset. Enterprise accounts can request cost-allocation tags to map charges
to internal cost centres.

## Prepaid credits

Credits can be purchased in advance at a discount (available for Scale and
Enterprise). Credits are applied before metered billing and expire 12 months
from purchase. Unused credits are non-refundable.

## Taxes

Nimbus adds applicable taxes (VAT, GST) based on your billing address at
checkout. Tax-exempt organisations can upload an exemption certificate in the
console under **Billing → Tax Settings**.
