# Picked-methods build steps, 2026-11-24

Pre-registration: [PREREG.md](PREREG.md) (C2, C3 in PR #105; D4 in PR #108, both merged before the runs). SYNTHETIC data only.

| Folder | Step | Result (computed) |
|---|---|---|
| `codyn/sim_c2.py` | #52 step 2: share-space compensation test | size 0.011 (bar 0.02-0.08), power 0.226 (bar 0.80). **Not passed; kill rule triggered**, share-space VR dropped. Official VR on shares 4.4e-17. |
| `codyn/bench_c3.py`, `bench_c3_numba.py` | #52 step 3: speed | NumPy 4.59 s for all metrics with a 999-draw null on 2,000 x 40 at 4 vCPU (bar 5 s); Numba null 0.076 s (60x), parity 2.7e-14. **Pass.** Rust not built. |
| `denselines/d4_power.py` | #56 step 4 input: branch-test power | Dip test power 0 (size ~0); mixture LRT power 0.82 at 500 series / 2 SD. |
