# Corrected smoke run — integration evidence (not results)

A `--fast` smoke of the corrected pipeline through the **executable** config
`configs/study_final_dissertation_v2.yaml` (not `study_full.yaml`), on PLEIA
temperature, writing to the disposable `runs/smoke_s1/` (git-ignored).

```
python -m src.run_study --config configs/study_final_dissertation_v2.yaml \
    --dataset pleia --fast --outputs outputs/final_dissertation_v2/runs/smoke_s1
```

| Field | Value |
|---|---|
| Exit code | **0** |
| Stages completed | 11 |
| Stages failed | **0** |
| Stages skipped | 0 |
| Wall clock | 442.3 s |
| fast_mode stamp | true |
| `outputs/full_study/` after run | unchanged (`0bf904c3…`) |

**What this validates:** the *wired* corrections integrate end-to-end without a
failed stage — the horizon embargo (A1), `target_lag_0` (B1), the causal
group-safe updated EnbPI (C1), and feature-schema persistence (B2, confirmed by
`runs/smoke_s1/pleia/data_profiles/feature_schema_h*.json`).

**What this does NOT establish, by design:** no metric from this run is a result;
`--fast` numbers are never quoted. The corrected *alert* stage still uses the old
primitives (the tested `alerts_corrected` module is not yet wired into the
orchestrator — see C3/D1/D4/E in `leakage_audit.json`), so alert numbers from this
smoke are not corrected numbers. The nested multi-seed full run remains gated
behind the end-to-end engine.
