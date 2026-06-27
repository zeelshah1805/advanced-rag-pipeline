# Nimbus Compliance and Certifications

## SOC 2 Type II

Nimbus is SOC 2 Type II certified. The audit covers the Security, Availability,
and Confidentiality trust service criteria. The audit period covers a rolling
12-month window; the most recent report was issued in Q4 2024.

Customers on the Scale and Enterprise plans can request a copy of the SOC 2
report by submitting a request through the support portal. A signed NDA is
required before the report is shared.

## HIPAA

Nimbus is **not** HIPAA compliant and must not be used to store, process, or
transmit Protected Health Information (PHI). This restriction applies to all
plans including Enterprise. There is no roadmap to add HIPAA compliance at
this time.

## GDPR

Nimbus is operated in accordance with the GDPR for customers using EU regions
(`eu-west-1`, `eu-central-1`). Key GDPR provisions supported:

- **Data residency** — data stored in EU regions never leaves the EU unless
  cross-region replication is explicitly configured.
- **Right to erasure** — fulfilled via the RPL purge API within 72 hours.
- **Data processing agreement (DPA)** — available for all paying customers from
  the console under **Settings → Legal → Download DPA**.
- **Sub-processors** — list of sub-processors is maintained at
  cirrus.io/sub-processors and updated 30 days before any change.

## ISO 27001

Nimbus is currently working toward ISO 27001 certification. Expected completion:
H2 2025.

## PCI DSS

Nimbus is not PCI DSS certified. Do not store, transmit, or process payment card
data in Nimbus.

## Data Processing Agreement (DPA)

All paid plans include a standard DPA. Enterprise customers may request a custom
DPA for specific contractual requirements. Contact your account manager.

## Penetration testing

Cirrus Systems conducts annual third-party penetration tests against the Nimbus
platform. Customers may request the executive summary of the most recent pen
test report (NDA required).

Enterprise customers may conduct their own penetration tests against their Nimbus
datasets, subject to prior written approval from Cirrus Systems. Tests that
target shared infrastructure are not permitted.

## Encryption standards

- **At rest**: AES-256. Always enabled; cannot be disabled.
- **In transit**: TLS 1.3. Older TLS versions are not accepted.
- **Key management**: Cirrus Systems manages encryption keys using a
  Hardware Security Module (HSM). Customer-managed keys (BYOK) are on the
  Enterprise roadmap for H1 2026.
