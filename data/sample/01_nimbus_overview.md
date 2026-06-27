# Nimbus Data Platform — Overview

Nimbus is a managed analytics platform for streaming and batch data. It was
first released as version 1.0 in March 2021 and reached version 2.0 in
September 2023. Nimbus is operated by Cirrus Systems and is offered as a fully
hosted service; there is no self-managed installation option.

The platform is organized around three core subsystems:

- The **Ingestion Gateway (IGW)** accepts incoming events over HTTP and gRPC.
  The IGW is the only public entry point for writes and enforces per-tenant
  rate limits before data reaches storage.
- The **Retention Policy Layer (RPL)** decides how long each class of data is
  kept. RPL is configured per dataset and is the component most often
  misconfigured by new users.
- The **Query Engine (QE)** executes analytical queries. The QE is a
  columnar, vectorized engine and is billed separately from storage.

Nimbus exposes all functionality through a single REST API and a command-line
tool called `nbx`. Every account is assigned a region at creation time and a
dataset cannot be moved between regions after it is created.

The default data retention for a new dataset is 30 days. Retention is governed
by the RPL and can be raised to a maximum of 365 days on the Scale plan, or
left unlimited on the Enterprise plan.
