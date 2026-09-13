# Research question and objective status

> Previously inspected test data remain previously inspected. A corrected rerun or additional seeds do not create an untouched holdout. Historical results require recomputation after the integration repairs; passing software tests does not establish scientific validity.

Core source: `outputs\final_dissertation_v2\runs\full_20260831_220811` — **historical_requires_rerun**.
Extension source: `outputs\final_dissertation_v2\runs\robx_full_20260902_080752` — **missing**.

Current numerical dissertation findings are not established by this report. See repository-root `INTEGRATION_REPAIR_REPORT.md` for repairs, unresolved design decisions and the required rerun.

- Point forecasting: multi-horizon Attention-LSTM/XGBoost evidence missing.
- Interval quality: comparable model-specific 90%/95% evidence missing.
- Alerting: historical estimates invalidated for current claims; rerun required.
- Leakage control: repaired paths tested; scientific design reconciliation pending.
- Robustness/recovery: completed full extension evidence missing.
