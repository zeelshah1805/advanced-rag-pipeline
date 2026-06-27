# Nimbus Python SDK

The official Python SDK for Nimbus is `nimbus-sdk`. It wraps the REST API and
provides async support via `asyncio`.

## Installation

```bash
pip install nimbus-sdk
```

Requires Python 3.9 or later. The SDK has no heavy dependencies: only `httpx`
for transport and `orjson` for fast JSON serialization.

## Authentication

```python
from nimbus import NimbusClient

client = NimbusClient(api_key="nbx_....", region="us-east-1")
```

The API key can also be read from the `NBX_API_KEY` environment variable if
`api_key` is omitted.

## Ingesting events

```python
events = [
    {"user_id": 42, "action": "click", "page": "/home"},
    {"user_id": 17, "action": "purchase", "amount": 99.99},
]
result = client.ingest("my-dataset", events)
print(result.accepted, result.rejected)
```

`client.ingest` batches automatically; if you pass more than 10,000 events it
splits the payload into multiple requests. Each call is synchronous; use
`AsyncNimbusClient` for non-blocking ingestion.

## Async ingestion

```python
import asyncio
from nimbus import AsyncNimbusClient

async def main():
    async with AsyncNimbusClient(api_key="nbx_...") as client:
        await client.ingest("my-dataset", events)

asyncio.run(main())
```

## Querying

```python
rows = client.query("SELECT user_id, COUNT(*) FROM my-dataset GROUP BY user_id")
for row in rows:
    print(row)
```

`client.query` handles pagination automatically and returns an iterator. For
large result sets that exceed memory, use `client.query_iter` which yields pages
lazily.

## Error handling

The SDK raises `nimbus.RateLimitError` on HTTP 429. It retries automatically
with exponential backoff up to 5 times by default. You can customise the retry
policy:

```python
from nimbus import RetryPolicy
client = NimbusClient(api_key="...", retry=RetryPolicy(max_attempts=10, max_wait=120))
```

Other exceptions:
- `nimbus.AuthError` — invalid or expired API key (HTTP 401/403).
- `nimbus.ValidationError` — schema validation failure in strict mode (HTTP 422).
- `nimbus.NimbusError` — base class for all SDK exceptions.

## Streaming ingest

For high-throughput producers, use the `StreamingIngestor` which maintains a
persistent connection and flushes on a configurable interval or batch size:

```python
from nimbus import StreamingIngestor

with StreamingIngestor(client, dataset="my-dataset", flush_interval=1.0, max_batch=5000) as s:
    for event in my_event_source():
        s.send(event)   # buffered; flushed automatically
```
