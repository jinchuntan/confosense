# RICO and BDG2: execution record before real fitting

Entry commit: `b26ee5b6a2cfb322b392e017e627bf3c96339c78`. Current authorization: `d334f2b36144b58434725d81c7de20c9324954b8:review/NEXT_TASK_MATCHED_RICO_BDG2.md`, supplied by the user. Branch: `review/matched-rico-bdg2-20260914`.

The [new authorization](../../smart_building_conformal/configs/matched_forecasting005_rico_bdg2_authorization.json) permits exactly RICO h5/f2/s42 then BDG2 h1/f2/s42: 16 tuning and four final learned fits, six point and twelve interval cells. The historical energy authorization and original no-fitting proposal remain unchanged. In each frozen protocol, top-level `parent_review_commit` and `instruction_commit` retain the original runner/design history; the nested `authorization` and [joint manifest](joint_pre_fit_manifest.json) explicitly identify the current authorizing instruction and actual entry commit.

## Demonstrated guard defect, repaired before any real fit

The original RICO freeze succeeded and matched the published data/roles. The first no-fitting readiness attempt failed because the generic fit-route guard intercepted `src.datasets.base.GroupPartitioner.fit`. That deterministic method uses only group IDs, start times and fixed fractions to assign chronological labels; it learns no predictor, normalization or signal-derived parameter. The new matched roles still come from the published whole-run design.

The guard now exempts only that exact Python code object. Other functions named `fit`, including a fake function in the same module, and the learned XGBoost/scikit-learn/model-unit routes remain forbidden. Fifteen no-fitting regression checks passed, including six focused checks for this exception. The previous tiny integration fits were not repeated; this task has zero synthetic fits.

The initial freeze protocols and failed readiness log are preserved. Both active protocols use fresh `v2` directories and the repaired source identity. No real fit had occurred, so no numerical result was invalidated or repeated. Historical energy/temperature/operational evidence retains its own source identity and byte hashes.

The first additional joint-preflight helper was launched from the repository root instead of `smart_building_conformal`. Relative raw-data paths entered the adapter's download path; that no-fit attempt was stopped (actual Windows exit 4294967295). The helper now explicitly uses the established project directory and the successful rerun has its own log. The separate repository-root download files are not scientific inputs or published artifacts; existing project data and hashes are retained.

## Fixed execution and acceptance

Before either real fit, freeze both v2 protocols, pass both fresh-support/readiness checks, verify every lazy sequence stays inside its original run/building, and commit source plus the joint manifest. The joint manifest binds exact schemas, memberships, dates, packages, source/config/data hashes and current authorization. All candidate, epoch-selection and own-model conformal rules remain unchanged.

Use the existing durable command logger and the compatible CPU environment. Retain one numerical/Torch thread, `n_jobs=1`, batch256, the 256 MiB epoch floor and 8 GiB disk check. The historical 3 GiB launch RAM value remains a recorded nonblocking reference. Execute RICO, independently validate saved streams and fitted artifacts, and verify zero-fit completed resume; then execute BDG2 under the same procedure. Rankings and achieved coverage do not govern continuation.

Expected RICO support is 12,932 fit / 4,452 calibration / 8,692 test rows, in 61/21/41 whole runs. Expected BDG2 support is 51,664 / 17,370 / 34,640 rows across the same ten buildings. These are matched forecasting masks. The different operational/challenge masks remain historical and unchanged.

Per-model checkpoints are atomic. No mid-fit recovery is promised. Every complete model is reused only under its verified identity; no completed valid fit is repeated for better scores. Full-study readiness and authorization for the remaining queue remain false.
