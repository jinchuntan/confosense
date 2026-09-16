# Durable progress and restart

Updated UTC: 2026-09-16T21:08:01.679553+00:00. Status: **science_and_evidence_complete**.

Restart the sole coordinator from the repository root:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/pleia_energy_context005_multiseed_20260915/coordinator.py
```

The exclusive lock prevents duplicate coordinators. An exact surviving logger or worker is adopted. Passed tasks are reused; known failed commands require investigation.

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
- seed_44/run: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T062044512204+0000_19834b5b\command.log.json`.
- seed_44/validate: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T071316751185+0000_efd356a0\command.log.json`.
- seed_44/resume: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T094103895984+0000_3aa3a9ce\command.log.json`.
- seed_45/run: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T095225319722+0000_f4e32e7f\command.log.json`.
- seed_45/validate: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T112041103643+0000_d24a31c5\command.log.json`.
- seed_45/resume: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T134820401014+0000_75de7ab9\command.log.json`.
- seed_46/run: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T140004349276+0000_ed9fb9d0\command.log.json`.
- seed_46/validate: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T154314716566+0000_bf848265\command.log.json`.
- seed_46/resume: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T181657766213+0000_cadef4ad\command.log.json`.
- final/analyze: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T191424024255+0000_7eefe6e0\command.log.json`.
- final/validate_aggregate: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T191626880475+0000_010338c1\command.log.json`.
- final/package_raw: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T200340756659+0000_d0214965\command.log.json`.
- final/update_documents: passed; actual exit 0; receipt `C:\Users\nigel\OneDrive\Desktop\GitHub\confosense\smart_building_conformal\outputs\conditional_context005\pleia_energy_f2_context005_multiseed_v1_coordinator\attempts\2026-09-16T210755538343+0000_35ff42a2\command.log.json`.
