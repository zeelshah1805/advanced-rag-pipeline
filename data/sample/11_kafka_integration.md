# Nimbus Kafka Integration

Nimbus can consume events directly from Apache Kafka topics using the
**Nimbus Kafka Connector**, a Kafka Connect sink connector distributed by
Cirrus Systems.

## Overview

The connector runs inside your existing Kafka Connect cluster and writes batches
of records from one or more Kafka topics to a Nimbus dataset. It handles
batching, back-pressure, and retry automatically and does not require any changes
to producers.

## Installation

Download the connector JAR from the Cirrus Systems plugin repository and place
it on the Kafka Connect worker's plugin path, or install via Confluent Hub:

```bash
confluent-hub install cirrus/nimbus-kafka-connector:latest
```

Restart the Kafka Connect worker after installation.

## Configuration

Create a connector instance via the Kafka Connect REST API:

```json
{
  "name": "nimbus-sink",
  "config": {
    "connector.class": "com.cirrus.nimbus.connect.NimbusSinkConnector",
    "tasks.max": "4",
    "topics": "clickstream,purchases",
    "nimbus.api.key": "${file:/opt/secrets/nimbus.properties:api_key}",
    "nimbus.region": "us-east-1",
    "nimbus.dataset": "prod-events",
    "nimbus.batch.size": "5000",
    "nimbus.flush.interval.ms": "2000",
    "nimbus.retry.max": "5"
  }
}
```

Key configuration properties:

| Property                    | Default | Description                                     |
|-----------------------------|---------|-------------------------------------------------|
| `nimbus.batch.size`         | 5000    | Max events per ingest call.                     |
| `nimbus.flush.interval.ms`  | 2000    | Max milliseconds between flushes.               |
| `nimbus.retry.max`          | 5       | Retry attempts on HTTP 429 or 5xx.              |
| `nimbus.strict.schema`      | false   | Enable strict-mode schema validation at source. |

## Topic-to-dataset mapping

By default all configured topics write to the same dataset. For a one-topic /
one-dataset mapping, deploy a separate connector instance per topic. Alternatively
use the `nimbus.topic.dataset.map` property:

```
nimbus.topic.dataset.map=clickstream:clicks-dataset,purchases:sales-dataset
```

## Dead-letter queue

Records that fail after all retries are routed to a Kafka dead-letter topic
(`<connector-name>-dlq` by default). Set `errors.deadletterqueue.topic.name`
to override. DLQ records include the original payload and error metadata as
headers.

## Schema Registry support

The connector integrates with Confluent Schema Registry. When
`value.converter=io.confluent.kafka.serializers.KafkaAvroDeserializer` is set,
Avro records are automatically converted to JSON before being sent to Nimbus.
JSON Schema and Protobuf converters are also supported.

## Monitoring the connector

The connector exposes JMX metrics under `com.cirrus.nimbus.connect`:
- `records-sent-total` — cumulative events successfully ingested.
- `records-failed-total` — events routed to the DLQ.
- `batch-latency-ms` — histogram of ingest call latency.

These metrics can be scraped by Prometheus via the JMX Exporter.
