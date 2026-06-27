# Nimbus Multi-Region Setup

Nimbus operates in multiple geographic regions. Each dataset is pinned to a
single region at creation time and cannot be moved. Understanding region
behaviour is important for latency, data residency, and compliance.

## Available regions

| Region ID     | Location              | Available plans        |
|---------------|-----------------------|------------------------|
| `us-east-1`   | Northern Virginia, US | Free, Scale, Enterprise|
| `us-west-2`   | Oregon, US            | Scale, Enterprise      |
| `eu-west-1`   | Dublin, Ireland       | Scale, Enterprise      |
| `eu-central-1`| Frankfurt, Germany    | Scale, Enterprise      |
| `ap-southeast-1` | Singapore          | Scale, Enterprise      |
| `ap-northeast-1` | Tokyo, Japan       | Enterprise             |

The Free plan is only available in `us-east-1`.

## Choosing a region

Choose the region closest to your data producers for lowest ingest latency.
For data residency requirements (e.g. GDPR), choose an EU region to ensure
data never leaves the EU. Cirrus Systems guarantees that data stored in an
EU region is never transferred to a non-EU region unless you explicitly enable
cross-region replication.

## Per-region API endpoints

Each region has a dedicated API endpoint. The API key prefix identifies the
region; the `nbx` CLI resolves the endpoint automatically. When calling the
REST API directly, use the regional base URL:

```
https://api.<region>.nimbus.io/v1/
```

For example, `https://api.eu-west-1.nimbus.io/v1/datasets`.

## API key region scoping

An API key issued in one region cannot access datasets in another region.
If you operate in multiple regions, create separate API keys per region. Use
descriptive key names (e.g. `prod-writer-eu-west-1`) to avoid confusion.

## Latency considerations

Nimbus enforces writes synchronously to at least two availability zones within
the same region before acknowledging. For the lowest end-to-end latency, deploy
producers in the same cloud provider and region as your Nimbus dataset. Writing
across continents typically adds 80–150 ms of round-trip latency.

## Data residency and compliance

Selecting `eu-central-1` (Frankfurt) ensures all data is stored and processed
within Germany, which satisfies stricter EU data residency requirements. The
`eu-west-1` region (Dublin) is within the EU but outside Germany and the DACH
regulatory zone.

## Cross-region replication (Enterprise only)

Enterprise customers can configure a read replica in a second region. See the
Disaster Recovery documentation for details. Cross-region replication does not
change the primary region for billing or data residency purposes.
