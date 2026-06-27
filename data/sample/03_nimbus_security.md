# Nimbus Security and Compliance

Nimbus encrypts all data at rest using AES-256 and all data in transit using
TLS 1.3. Encryption at rest is always on and cannot be disabled.

## Authentication

Access to the REST API and the `nbx` CLI is authenticated with API keys. Each
API key is scoped to a single region and carries one of three roles: `reader`,
`writer`, or `admin`. The `admin` role is required to change Retention Policy
Layer (RPL) settings. API keys can be rotated at any time from the console; a
rotated key remains valid for a 24-hour grace period.

On the Enterprise plan, single sign-on (SSO) via SAML can replace API keys for
human users. Service accounts continue to use API keys regardless of plan.

## Compliance

Nimbus is SOC 2 Type II certified. The platform is **not** HIPAA compliant and
must not be used to store protected health information. GDPR data-deletion
requests are honored through the RPL's purge API, which performs a hard delete
within 72 hours.

## Audit logging

Every administrative action is written to an immutable audit log. Audit logs are
retained for 90 days on the Scale plan and for 1 year on the Enterprise plan.
The Free plan does not include audit logging.
