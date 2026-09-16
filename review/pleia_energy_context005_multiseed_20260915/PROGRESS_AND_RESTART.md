# Durable progress and restart

Last live coordinator update: 2026-09-15T03:24:22.408617+00:00. Status: **INTERRUPTED_BEFORE_RECOVERY**.

Restart the sole coordinator from the repository root:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```

The exact Windows interruption is documented in [RECOVERY_STATUS.md](RECOVERY_STATUS.md). The exclusive lock prevents duplicate coordinators. An exact surviving logger or worker is adopted. Passed tasks are reused; the bounded recovery helper preserves the recorded seed-44 nonzero receipt and resumes only its hash-compatible incomplete run.

- seed_43/freeze: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233749141242+0000_2d99d1d4\command.log.json`.
- seed_43/readiness: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233757260524+0000_a1bc53e5\command.log.json`.
- seed_44/freeze: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233803399849+0000_9895c233\command.log.json`.
- seed_44/readiness: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233811558050+0000_2273569f\command.log.json`.
- seed_45/freeze: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233817691097+0000_07da913d\command.log.json`.
- seed_45/readiness: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233823812102+0000_2da04fa6\command.log.json`.
- seed_46/freeze: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233829956849+0000_5ca44203\command.log.json`.
- seed_46/readiness: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233838102686+0000_d9461cad\command.log.json`.
- batch/preflight: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233844222430+0000_9d3be30e\command.log.json`.
- seed_43/run: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-14T233930757651+0000_aeffeebe\command.log.json`.
- seed_43/validate: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-15T004141598976+0000_07e011c6\command.log.json`.
- seed_43/resume: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-15T021916817689+0000_a19df4c1\command.log.json`.
