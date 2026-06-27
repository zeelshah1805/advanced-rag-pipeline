# Nimbus Changelog

## Version 2.0 — September 2023

- Added the vectorized Query Engine (QE), replacing the row-based engine from
  the 1.x line. Analytical queries are typically 4x faster as a result.
- Introduced per-dataset retention configuration through the Retention Policy
  Layer. In version 1.x, retention was a single account-wide setting.
- Raised the Scale plan ingestion limit from 5,000 to 10,000 events per second.
- Added VPC peering for Enterprise customers.
- Removed the legacy `nbx export` command; use `nbx query` with output
  redirection instead.

## Version 1.5 — June 2022

- Added SAML single sign-on for Enterprise.
- Introduced the immutable audit log.
- Increased Free plan storage from 2 GB to 5 GB.

## Version 1.0 — March 2021

- Initial release with the Ingestion Gateway, row-based query engine, and a
  fixed 30-day retention for all datasets.
- Free and Enterprise plans only; the Scale plan was added later in version 1.2.
