# Kumo burn-in schema smoke — v2 review B3

## Live verified response (`kumo_burnin_smoke_v2_live.json`)

Recorded from a real POST to
`https://ai.api.nvidia.com/v1/structured-data/nvidia/kumo-relational/predictions`
on burn-in origin 2008-12-19 / target 2008-12-26 (pinned zip sha256 `16805f2c…`),
using the harness `kumo.build_payload` + `urllib_transport` + `KumoClient._parse`
path. Mode `fast`, 2 entities (small-entity smoke for latency), HTTP 200, response
parsed as finite `predictions[].prediction` values. Date and endpoint are stored
in the fixture (`recorded_utc`, `recorded_date_america_new_york`, `endpoint`).

The first live attempts against the pre-fix schema returned **HTTP 422**
`INVALID_SCHEMA` (`Kumo Relational requires a declared 'instance_id' column` on
`schema.related_tables.entities.columns`). `build_payload` now emits
instance-scoped entity rows that declare `instance_id`, matching the working
NIM client layout. That schema fix is what made the live 200 possible.

Key from `NVIDIA_API_KEY` only; no credential or request/response headers are
saved. Not a trial, replication, or OOS run.

## Prior timeout evidence (`kumo_burnin_smoke_v2.json`)

One earlier live POST in `best` mode with the pre-fix 24-entity schema hit the
300s read timeout before any HTTP status. Kept as historical evidence that the
first attempt did not fabricate a response. `parser_verified` is false there.

B1/B2 choices are in `docs/tracks/fed-cp-ot/prereg_v2/IMPLEMENTATION_CHOICES_v2.md`;
verify the expanded manifest from repository root with:

```sh
sha256sum -c tracks/fed-cp-ot/prereg/PIN_v2.txt
```

Approval and approval-hash pinning remain separate steps. Before OOS, the burn-in
replication job must pass once on **main after merge**.
