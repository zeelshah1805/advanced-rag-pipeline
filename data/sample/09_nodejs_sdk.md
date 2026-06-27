# Nimbus Node.js SDK

The official Node.js SDK is `@cirrus/nimbus`. It targets Node.js 18+ and ships
as both CommonJS and ESM.

## Installation

```bash
npm install @cirrus/nimbus
```

## Initialising the client

```js
import { NimbusClient } from "@cirrus/nimbus";

const client = new NimbusClient({
  apiKey: process.env.NBX_API_KEY,
  region: "eu-west-1",
});
```

## Ingesting events

```js
await client.ingest("my-dataset", [
  { userId: 1, action: "view" },
  { userId: 2, action: "click" },
]);
```

Events are automatically batched. Payloads larger than 10,000 events or 10 MB
are split across multiple requests. All requests are retried on HTTP 429 with
truncated exponential backoff.

## Querying

```js
const result = await client.query(
  "SELECT action, COUNT(*) AS n FROM `my-dataset` GROUP BY action ORDER BY n DESC"
);
for (const row of result.rows) {
  console.log(row.action, row.n);
}
```

Pagination is handled automatically. Use `client.queryStream` for a Node.js
`Readable` stream that yields rows one at a time without buffering the full
result set.

## TypeScript support

The SDK ships full TypeScript declarations. `IngestResult`, `QueryResult`, and
all error classes are exported. Generic types are available for typed event
schemas:

```ts
interface ClickEvent {
  userId: number;
  page: string;
  ts: string;
}
const result = await client.ingest<ClickEvent>("clicks", events);
```

## Error types

| Class                     | HTTP status | Meaning                          |
|---------------------------|-------------|----------------------------------|
| `NimbusAuthError`         | 401/403     | Invalid or missing API key       |
| `NimbusRateLimitError`    | 429         | Rate limit exceeded              |
| `NimbusValidationError`   | 422         | Strict-mode schema violation     |
| `NimbusServerError`       | 5xx         | Transient server error           |

All inherit from `NimbusError`.

## Connection pooling

The client uses an internal HTTP/2 connection pool. For serverless environments
that create a new client per invocation, pass `keepAlive: false` to skip pool
initialisation and reduce cold-start overhead.

## Webhook delivery (Enterprise)

Enterprise accounts can register a webhook URL to receive ingest acknowledgement
events asynchronously. See the Webhooks documentation for setup. The Node.js SDK
provides `NimbusWebhookReceiver` to verify webhook signatures:

```js
import { NimbusWebhookReceiver } from "@cirrus/nimbus";
const receiver = new NimbusWebhookReceiver(process.env.WEBHOOK_SECRET);
const event = receiver.parse(rawBody, signatureHeader);
```
