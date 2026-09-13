# Computational evidence status

> Previously inspected test data remain previously inspected. A corrected rerun or additional seeds do not create an untouched holdout. Historical results require recomputation after the integration repairs; passing software tests does not establish scientific validity.

Core source: `outputs\final_dissertation_v2\runs\full_20260831_220811` — **historical_requires_rerun**.
Extension source: `outputs\final_dissertation_v2\runs\robx_full_20260902_080752` — **missing**.

Current numerical dissertation findings are not established by this report. See repository-root `INTEGRATION_REPAIR_REPORT.md` for repairs, unresolved design decisions and the required rerun.

No validated Attention-LSTM/XGBoost resource comparison is available. Do not extrapolate full-run cost from smoke timings. The next comparison must measure tuning, refitting and inference separately, plus process peak memory, on matched support. PyTorch in the existing environment is CPU-only.
