# Nimbus SLA and Support

## Service Level Agreements

Nimbus defines uptime SLAs for the Ingestion Gateway and the Query Engine
separately. The SLA covers availability of the service endpoints, not query
performance.

| Plan       | IGW uptime SLA | QE uptime SLA | Support                        |
|------------|----------------|---------------|--------------------------------|
| Free       | None           | None          | Community forum only           |
| Scale      | 99.9%          | 99.9%         | Email, 24-hour response target |
| Enterprise | 99.99%         | 99.99%        | Dedicated channel, 1-hour P1   |

**99.9% uptime** corresponds to at most 8.7 hours of downtime per year (or
~43 minutes per month). **99.99% uptime** corresponds to at most 52 minutes
per year (~4.4 minutes per month).

Planned maintenance windows are excluded from SLA calculations. Cirrus Systems
provides 48 hours advance notice for planned maintenance via the status page
and email.

## SLA credits

If Nimbus fails to meet the stated SLA in a calendar month, you are eligible
for a service credit:

| Uptime achieved | Credit (% of monthly bill) |
|-----------------|---------------------------|
| 99.0–99.9%      | 10%                        |
| 95.0–99.0%      | 25%                        |
| < 95.0%         | 50%                        |

Credits must be claimed within 30 days of the end of the affected month by
submitting a request to support with the incident reference numbers.

## Support channels

### Community forum
Available to all plans. Public forum at community.nimbus.io. Response times
are best-effort from the Nimbus team and other community members.

### Email support (Scale)
Submit tickets at support.nimbus.io. Target first response within 24 hours for
P2/P3 issues. P1 (production down) response target is 4 hours on the Scale plan.

### Dedicated support channel (Enterprise)
A private Slack or Teams channel with the Cirrus Systems engineering team.
P1 response target: 1 hour, 24/7. Includes a named Technical Account Manager
(TAM) for quarterly reviews, onboarding assistance, and architecture guidance.

## Incident communication

All incidents are posted to status.nimbus.io. Subscribe to status updates via
email, RSS, or webhook. During an active P1 incident, Cirrus Systems posts
updates at least every 30 minutes.

## Supported environments

Nimbus officially supports:
- Python 3.9+ with `nimbus-sdk`.
- Node.js 18+ with `@cirrus/nimbus`.
- Kafka Connect 3.0+ with the Nimbus Kafka Connector.
- `nbx` CLI on macOS 12+, Ubuntu 20.04+, Debian 11+, Windows 10+.

Older versions receive best-effort support only.
