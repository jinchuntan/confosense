# Temperature seeds 43--46 preflight evidence

- [Preflight report](PREFLIGHT_REPORT.md)
- [Authoritative readiness decision](PREFLIGHT_READINESS_V2.json)
- [Preservation baseline](PRESERVATION_BASELINE.json)
- [Resource and capacity budget](RESOURCE_BUDGET.json)
- [Draft-design preflight](DESIGN_PREFLIGHT.json)
- [Manifest and identity comparison](MANIFEST_COMPARISON.csv)
- [Explicit-path validator v2](candidate_validate_v2.py)
- [Focused-test source](test_candidate_v2.py)
- [Authoritative focused-test receipt](focused_tests_v2/FOCUSED_TEST_RECEIPT.json)
- [Authoritative focused-test rows](focused_tests_v2/focused_test_results.csv)
- [Future commands and recovery plan](FUTURE_COMMANDS.json)
- [Preparation script](prepare_preflight.py)
- [Draft-freeze script](freeze_preflight.py)
- [Evidence finalizer](finalize_preflight.py)
- [Package verifier](verify_preflight.py)
- [Authoritative package verification receipt](PACKAGE_VERIFICATION_V2.json)
- [Preserved failed self-link verification attempt](PACKAGE_VERIFICATION.json)
- [Attempts and supersession note](ATTEMPTS_AND_SUPERSESSION.md)

Draft manifests:

- [Seed 43](pleia_f2_s43_C_v1_draft_manifest.json)
- [Seed 44](pleia_f2_s44_C_v1_draft_manifest.json)
- [Seed 45](pleia_f2_s45_C_v1_draft_manifest.json)
- [Seed 46](pleia_f2_s46_C_v1_draft_manifest.json)

Review-local draft design directories are under [`draft_designs/`](draft_designs/). They are preflight artifacts with `execution_authorized=false`, not production protocols.

The successful [`focused_tests/`](focused_tests/) and [PREFLIGHT_READINESS.json](PREFLIGHT_READINESS.json) are preserved provisional evidence. They are superseded by the V2 artifacts above, which add immutable identity verification of the delegated audited validator source.
