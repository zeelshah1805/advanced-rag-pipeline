# nbx CLI — Advanced Usage

This document covers advanced `nbx` features beyond the basics in the CLI
reference. Familiarity with the core commands (`auth`, `ingest`, `query`,
`purge`) is assumed.

## Configuration profiles

`nbx` supports named profiles for managing multiple regions or accounts:

```bash
nbx auth login --key nbx_us_prod --profile us-prod
nbx auth login --key nbx_eu_prod --profile eu-prod
nbx --profile eu-prod dataset list
```

The active profile can be set with `NBX_PROFILE` environment variable or the
`--profile` flag on any command.

## Output formats

Most `nbx` commands accept `--output` to control format:

| Format  | Flag                | Description                                |
|---------|---------------------|--------------------------------------------|
| Table   | `--output table`    | Human-readable aligned table (default).    |
| JSON    | `--output json`     | Pretty-printed JSON.                       |
| NDJSON  | `--output ndjson`   | One JSON object per line; pipe-friendly.   |
| CSV     | `--output csv`      | Comma-separated; includes header row.      |

Example:
```bash
nbx query "SELECT * FROM clicks LIMIT 10" --output csv > clicks.csv
```

## Piping and scripting

`nbx` is designed for shell pipelines:

```bash
# Count events in the last 24h
nbx query "SELECT COUNT(*) AS n FROM events WHERE _received_at > NOW() - INTERVAL '1 day'" \
  --output json | jq '.rows[0].n'

# Ingest from a process that produces NDJSON
my-producer | nbx ingest my-dataset --file -
```

`--file -` reads from stdin, allowing `nbx ingest` to be the sink in a pipeline.

## Schema management

```bash
nbx schema set my-dataset --file ./schema.json   # upload/replace schema
nbx schema get my-dataset                         # download current schema
nbx schema validate my-dataset --file events.ndjson  # validate locally, no API call
```

`schema validate` performs client-side validation against the current schema
without sending data to the IGW. Useful in CI to catch schema violations before
deployment.

## View management

```bash
nbx view list                                   # list all views
nbx view create hourly_totals --dataset events \
  --sql "SELECT TIMEBUCKET(_received_at,'1h') h, SUM(amount) total FROM events GROUP BY h" \
  --refresh 10m
nbx view refresh hourly_totals                  # force an immediate refresh
nbx view delete hourly_totals
```

## Dataset cloning

Clone a dataset (metadata and schema only; no data is copied):
```bash
nbx dataset clone source-dataset --name dest-dataset
```

Useful for creating a staging dataset with the same schema as production.

## Dry-run mode

Any ingest command accepts `--dry-run` to validate the file format and schema
without sending data to the IGW:
```bash
nbx ingest my-dataset --file events.ndjson --dry-run
```

This validates NDJSON structure and (if strict schema is enabled) schema
compliance without consuming ingest quota or incurring costs.

## Completion scripts

Generate shell completion:
```bash
nbx completion bash >> ~/.bashrc    # Bash
nbx completion zsh  >> ~/.zshrc     # Zsh
nbx completion fish > ~/.config/fish/completions/nbx.fish  # Fish
```
