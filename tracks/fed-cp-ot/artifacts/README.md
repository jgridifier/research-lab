# Kumo burn-in schema smoke — v2 review B3

`kumo_burnin_smoke_v2.json` records exactly one live POST to NVIDIA NIM in
`best` mode, using the pinned research archive (sha256 `16805f2c…`), origin
2008-12-19 and target 2008-12-26. The request is preserved in full, including
its regression schema, context and 24 unlabelled prediction instances. The key
came from `NVIDIA_API_KEY`; no credential or request/response headers are saved.

**Outcome: timeout, response schema unverified.** The existing 300-second read
timeout expired before an HTTP status or body arrived. `response` and `status`
are therefore null, not fabricated response evidence. The timeout metadata was
added from the invocation traceback after the original smoke's `finally` block
saved the request. No second call or retry was made. B3 remains unresolved as a
successful live response-schema check; this artifact is not statistical evidence,
a replication, or an OOS trial.

The dedicated `fed_cp_ot.kumo_smoke` entry point checks the target before any
I/O, rejects OOS targets (including origin 2008-12-26 / target 2009-01-02), parses
with a burn-in cutoff at the origin, and makes one transport call with no retry.
An existing output file prevents a repeat request at that path. Tests cover the
wall, retries, secret redaction, timeout evidence and the committed payload.
The smoke does not invoke the harness, score outcomes, or write a trial log.

B1/B2 choices are in `docs/tracks/fed-cp-ot/prereg_v2/IMPLEMENTATION_CHOICES_v2.md`;
verify the expanded manifest from repository root with:

```sh
sha256sum -c tracks/fed-cp-ot/prereg/PIN_v2.txt
```

The manifest is prepared in this review revision as requested; approval and
approval-hash pinning remain separate steps. Before OOS, the burn-in replication
job must pass once on **main after merge**. A local pass does not satisfy that gate.
