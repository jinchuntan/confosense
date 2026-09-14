# Supplemental no-fit DSCP check

The pre-fit acceptance remains unchanged. One additional check strengthened the held-out-truth test by passing perturbed test outcomes through the actual joint-origin input assembly, loading the saved synthetic calibrator, and checking identical assignments and lower/upper bounds at both levels. The calibrator's serialized state and every saved synthetic artifact remained byte-identical. All learned and calibrator fitting was forbidden.

The first attempt exited 1 because this additional reader expected `y_true`, whereas issued streams save the outcome as `observed`. Correcting that reader alias resolved the check: the second attempt exited 0, with one test passed. Neither attempt changed scientific source, protocols, fitted objects, or real-run settings. The failed receipt is preserved.

There are now **38 distinct resolved checks**: the 37 pre-fit checks plus this additional check. No synthetic fits were repeated. [Machine-readable acceptance and actual receipts](SUPPLEMENTAL_ACCEPTANCE.json), [test source](test_truth_independence.py), [original acceptance](SYNTHETIC_ACCEPTANCE.json).
