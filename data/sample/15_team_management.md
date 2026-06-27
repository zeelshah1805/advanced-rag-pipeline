# Nimbus Team Management and RBAC

Nimbus uses role-based access control (RBAC) to govern what each API key and
human user can do. Access is scoped by region; an API key issued in `us-east-1`
cannot access resources in `eu-west-1`.

## Roles

There are three built-in roles:

| Role    | Capabilities                                                          |
|---------|-----------------------------------------------------------------------|
| `reader` | Read datasets, run queries, view audit logs.                         |
| `writer` | All reader permissions plus ingest events to any dataset.            |
| `admin`  | All writer permissions plus manage API keys, change RPL settings,    |
|          | create/delete datasets, trigger purges, manage team members.         |

The `admin` role is required to change Retention Policy Layer (RPL) settings
and to run `nbx purge`.

## API keys

API keys are created and managed in the console under **Settings → API Keys**.
Each key carries exactly one role and is scoped to one region. Key naming is
free-form; a descriptive name is recommended (e.g. `ci-prod-writer`).

- **Rotation:** rotate a key at any time. The old key remains valid for a
  24-hour grace period, then expires. The grace period ensures zero-downtime
  rotation for deployed services.
- **Expiry:** keys can be given an optional expiry date. Expired keys return
  HTTP 401.
- **Audit:** all API key usage is logged in the audit log with the key name,
  not the secret, for traceability.

## Human users (Enterprise SSO)

On the Enterprise plan, human users authenticate via SAML SSO. Each user is
assigned a role in your identity provider (IdP) and the Nimbus SAML attribute
mapping determines which Nimbus role they receive.

Service accounts and CI pipelines continue to use API keys regardless of
whether SSO is enabled.

## Inviting team members

Admins can invite team members via email from **Settings → Team**. Invited users
receive an email with a link to set up their console access. A team member's
role can be changed at any time by an admin; the change takes effect immediately.

## Sub-accounts (Enterprise)

Enterprise organisations can create sub-accounts for business units or
environments (e.g. staging, production). Each sub-account has its own datasets,
API keys, billing, and RBAC. A parent-account admin can view and manage all
sub-accounts from the parent console.

## Audit log access

The full audit log (all admin actions by all users and API keys) is accessible
to `admin` role users only. `reader` and `writer` roles see only their own
activity.
