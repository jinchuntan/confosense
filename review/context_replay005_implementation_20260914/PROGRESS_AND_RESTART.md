# Completed progress and exact restart

Both synthetic freeze/readiness/run/validate/resume workflows completed. All ten final action receipts have actual exit 0. Two failed numeric-reader validation attempts are retained; they caused no extra fitting. The sequential coordinator is complete and has no active worker.

To reconcile an interrupted copy or verify completed coordinator state on this branch, run from the repository root:

```powershell
& C:/cfs_venv/Scripts/python.exe -B review/context_replay005_implementation_20260914/coordinator.py --version v1
```

The coordinator adopts exact surviving worker identities, skips passed stages and refuses a known unresolved failure. Scientific COMPLETE trees are preserved. The explicit numeric-reader compatibility applies only to completed PLEIA validation/resume and cannot authorize execution under changed source. Current RICO and real-proposal v3 freezes bind the final source.

To verify either completed unit independently again, run from `smart_building_conformal`; omit a receipt path to print the zero-fit result without overwriting evidence:

```powershell
& C:/cfs_venv/Scripts/python.exe -B -m src.conditional_context005 resume --design protocols/conditional_context005/synthetic_pleia_energy_v1 --out outputs/conditional_context005/synthetic_pleia_energy_v1 --readiness protocols/conditional_context005/synthetic_pleia_energy_v1/readiness.json
& C:/cfs_venv/Scripts/python.exe -B -m src.conditional_context005 resume --design protocols/conditional_context005/synthetic_rico_v1 --out outputs/conditional_context005/synthetic_rico_v1 --readiness protocols/conditional_context005/synthetic_rico_v1/readiness.json
```

No execution blocker remains for this implementation package. The separately proposed energy mask still needs scientific adoption. The single next execution proposal is the exact PLEIA-energy fold-2/seed-42/h1 C unit in FIRST_CONDITIONAL_CONTEXT_RUN_PROPOSAL.md. It is not launched; its future coordinator requires a new user execution instruction.
