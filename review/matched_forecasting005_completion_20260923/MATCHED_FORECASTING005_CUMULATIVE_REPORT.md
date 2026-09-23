# Matched-forecasting amendment-005 cumulative completion

All 125 authorized outstanding paired units completed and passed the existing validator plus completed zero-fit resume. Combined with 70 preserved units, the declared own-model comparison is 195/195 units, 585/585 point cells and 1,170/1,170 interval cells.

The new execution used 1,000 tuning and 250 final learned fits, exactly the authorized 1,250-fit ceiling. Persistence used zero learned fits; historical units were not refitted.

## Equal-fold descriptive results

Values below first average five training seeds within each outer fold, then average the three overlapping folds equally. They are descriptive and are not population intervals.

| dataset | physical_minutes | model | mae | rmse | coverage90 | coverage95 | mpiw95 | winkler95 | process_cpu_seconds |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| bdg2 | 60 | attention_lstm | 18.077 | 34.1176 | 0.903532 | 0.952103 | 134.665 | 220.454 | 819.979 |
| bdg2 | 60 | persistence | 19.3383 | 39.3162 | 0.901954 | 0.950731 | 162.575 | 258.425 | 0.0197917 |
| bdg2 | 60 | xgboost | 17.0722 | 33.3722 | 0.903236 | 0.950857 | 131.48 | 217.662 | 10.099 |
| bdg2 | 180 | attention_lstm | 29.0846 | 55.0986 | 0.904523 | 0.952543 | 214.23 | 360.477 | 615.174 |
| bdg2 | 180 | persistence | 38.6731 | 73.7268 | 0.906908 | 0.951607 | 344.937 | 484.89 | 0.0208333 |
| bdg2 | 180 | xgboost | 25.8373 | 49.4915 | 0.903326 | 0.951162 | 195.425 | 322.77 | 9.625 |
| bdg2 | 360 | attention_lstm | 36.8069 | 68.1391 | 0.907184 | 0.954457 | 269.041 | 447.613 | 456.63 |
| bdg2 | 360 | persistence | 65.9485 | 112.674 | 0.906251 | 0.951054 | 507.853 | 685.263 | 0.0177083 |
| bdg2 | 360 | xgboost | 31.6615 | 60.7135 | 0.903996 | 0.951629 | 238.115 | 398.155 | 9.58333 |
| pleia | 10 | attention_lstm | 1.65646 | 1.96141 | 0.662373 | 0.717964 | 4.54318 | 22.1368 | 211.706 |
| pleia | 10 | persistence | 0.220548 | 0.329378 | 0.92618 | 0.961812 | 1.46667 | 1.92278 | 0.00651042 |
| pleia | 10 | xgboost | 1.23949 | 1.52108 | 0.651566 | 0.712473 | 2.97782 | 18.9664 | 3.7151 |
| pleia | 30 | attention_lstm | 1.91127 | 2.21752 | 0.652919 | 0.709323 | 5.0641 | 23.3286 | 194.953 |
| pleia | 30 | persistence | 0.378352 | 0.571401 | 0.914808 | 0.954712 | 2.33333 | 3.41661 | 0.003125 |
| pleia | 30 | xgboost | 1.82992 | 2.12851 | 0.602019 | 0.686976 | 4.15665 | 23.4924 | 3.71068 |
| pleia | 60 | attention_lstm | 2.57599 | 2.90686 | 0.629488 | 0.692487 | 6.69515 | 26.2268 | 123.796 |
| pleia | 60 | persistence | 0.539464 | 0.802209 | 0.908146 | 0.952391 | 3.26667 | 4.77927 | 0.00755208 |
| pleia | 60 | xgboost | 2.35839 | 2.67218 | 0.592302 | 0.67783 | 5.19963 | 27.0291 | 3.67943 |
| pleia_energy | 10 | attention_lstm | 0.144415 | 1.9968 | 0.793112 | 0.847382 | 0.748567 | 2.68104 | 134.805 |
| pleia_energy | 10 | persistence | 0.172986 | 2.79431 | 0.806301 | 0.858015 | 0.875 | 3.78558 | 0.00729167 |
| pleia_energy | 10 | xgboost | 0.140294 | 1.99396 | 0.844947 | 0.908941 | 0.794915 | 2.28412 | 3.65 |
| pleia_energy | 30 | attention_lstm | 0.155476 | 2.00523 | 0.804208 | 0.861264 | 0.827348 | 2.74038 | 91.175 |
| pleia_energy | 30 | persistence | 0.171523 | 2.79832 | 0.812862 | 0.858552 | 0.885417 | 3.90412 | 0.0104167 |
| pleia_energy | 30 | xgboost | 0.144604 | 1.99681 | 0.844692 | 0.889225 | 0.794972 | 2.53642 | 3.49792 |
| pleia_energy | 60 | attention_lstm | 0.166584 | 2.01093 | 0.808098 | 0.865248 | 0.90328 | 2.85467 | 72.5562 |
| pleia_energy | 60 | persistence | 0.177722 | 2.79723 | 0.805426 | 0.855693 | 0.921875 | 3.97037 | 0.00625 |
| pleia_energy | 60 | xgboost | 0.153077 | 2.00386 | 0.824915 | 0.877509 | 0.821337 | 2.76662 | 3.48542 |
| rico | 5 | attention_lstm | 1.29258 | 1.50905 | 0.665481 | 0.696986 | 3.16546 | 27.1035 | 121.746 |
| rico | 5 | persistence | 0.0989968 | 0.163407 | 0.904996 | 0.951762 | 0.666667 | 1.05819 | 0.009375 |
| rico | 5 | xgboost | 0.16637 | 0.265535 | 0.747512 | 0.84181 | 0.524468 | 2.38406 | 4.78333 |
| rico | 15 | attention_lstm | 1.41709 | 1.65851 | 0.648017 | 0.68588 | 3.22113 | 28.9863 | 110.406 |
| rico | 15 | persistence | 0.28201 | 0.446723 | 0.885852 | 0.93483 | 1.8 | 2.9737 | 0.00833333 |
| rico | 15 | xgboost | 0.348876 | 0.489638 | 0.784753 | 0.873058 | 1.48825 | 3.20291 | 4.67708 |
| rico | 30 | attention_lstm | 1.55736 | 1.8323 | 0.623764 | 0.665263 | 3.46635 | 31.2892 | 89.4208 |
| rico | 30 | persistence | 0.530428 | 0.815936 | 0.879884 | 0.934226 | 3.26667 | 5.39169 | 0.0104167 |
| rico | 30 | xgboost | 0.615327 | 0.842615 | 0.785592 | 0.883209 | 2.74116 | 5.17891 | 4.44792 |
| rico | 60 | attention_lstm | 1.73661 | 2.08818 | 0.621974 | 0.668924 | 4.1056 | 30.9387 | 68.7885 |
| rico | 60 | persistence | 0.976071 | 1.41641 | 0.871767 | 0.929214 | 5.53333 | 8.95167 | 0.00729167 |
| rico | 60 | xgboost | 0.913776 | 1.31171 | 0.801324 | 0.893425 | 4.0799 | 8.17449 | 3.85417 |

## Validation and computation

New run commands used 9.628 wall hours and 9.420 process CPU hours. Independent per-unit validation added 0.562 wall hours; completed resumes added 0.441 hours. Peak lifetime RSS was 1187.3 MiB.

All saved metric arithmetic, common target identities, finite-sample radii, inner selection, final epochs, native seeds, serialized-model reload predictions, original-group/RICO-phase reconstructions and run-tree integrity passed.

## Evidence preservation

The 125 per-unit raw archives contain 4,375 files (2,608,609,216 uncompressed bytes; 2,498,898,475 archive bytes). Ten additional verified support archives preserve all frozen protocols, process receipts, and coordinator attempts, receipts and journals. Each archive is below the established 95 MiB limit; tracked manifests provide exact paths, sizes and SHA-256 hashes. The scoped Git recovery bundle is recorded separately in the delivery receipt.

## Interpretation limits and remaining obligations

Outer folds overlap, model seeds repeat training on the same fold support, and persistence aliases are deterministic. Population intervals therefore remain unavailable under the established design; no alternative inference was introduced. RICO acquisition phases and recurring known BDG2 buildings retain their earlier limitations.

This closes only the declared own-model matched comparison. The separate 1,950-cell CQR/EnbPI/DSCP method matrix, seasonal computations, operational-grid work, and robustness/contamination/recovery obligations remain incomplete. Full-study readiness remains false.
