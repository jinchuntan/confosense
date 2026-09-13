# Matched failure diagnosis: preserved fold-2 seed-42 evidence

No new unresolved correctness defect was demonstrated. All thirteen existing task/horizon units were inspected without fitting or repeating historical tuning. Existing exact model-reload, support, normalization, selection and interval-arithmetic checks remain valid. Measured distribution changes and prediction bias warrant reporting; they do not identify their causal mechanism. The authorized seed replication may proceed with unchanged scientific settings.

## Observed bias and distributions

Final fitting predictions below are new inference using the preserved fitted objects; calibration/test and learned inner-validation predictions are saved streams. Inner training predictions were not saved and are not recreated by refitting. Current role boundaries and target ranges are in [role_target_ranges.csv](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/role_target_ranges.csv); every permitted flat-feature range is in [permitted_feature_ranges.csv](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/permitted_feature_ranges.csv). These describe available inputs at the origin; flat and sequence representations remain distinct.

### pleia

| horizon | model | role | n | truth_mean | bias | mae | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | persistence | calibration | 4953 | 24.0969 | -0.00113063 | 0.26804 | 0.372473 |
| 1 | persistence | test | 9907 | 28.9392 | -0.000393661 | 0.239376 | 0.336674 |
| 1 | persistence | fit | 14858 | 20.1205 | -0.000296137 | 0.218441 | 0.343975 |
| 1 | xgboost | calibration | 4953 | 24.0969 | -0.320535 | 0.471811 | 0.639275 |
| 1 | xgboost | test | 9907 | 28.9392 | -2.23702 | 2.26181 | 2.66629 |
| 1 | xgboost | fit | 14858 | 20.1205 | 7.48363e-05 | 0.211681 | 0.303729 |
| 1 | attention_lstm | calibration | 4953 | 24.0969 | -0.545636 | 0.674197 | 0.955131 |
| 1 | attention_lstm | test | 9907 | 28.9392 | -3.02519 | 3.03129 | 3.33861 |
| 1 | attention_lstm | fit | 14858 | 20.1205 | 0.0691373 | 0.230053 | 0.334036 |
| 3 | persistence | calibration | 4952 | 24.0953 | -0.00325121 | 0.432532 | 0.598448 |
| 3 | persistence | test | 9907 | 28.9392 | -0.00108004 | 0.391592 | 0.565536 |
| 3 | persistence | fit | 14855 | 20.1203 | -0.00105015 | 0.387654 | 0.588167 |
| 3 | xgboost | calibration | 4952 | 24.0953 | -0.680981 | 0.874817 | 1.15583 |
| 3 | xgboost | test | 9907 | 28.9392 | -3.50921 | 3.52336 | 3.91737 |
| 3 | xgboost | fit | 14855 | 20.1203 | 0.000521597 | 0.340473 | 0.477711 |
| 3 | attention_lstm | calibration | 4952 | 24.0953 | -0.792321 | 0.999611 | 1.32124 |
| 3 | attention_lstm | test | 9907 | 28.9392 | -3.75154 | 3.76055 | 4.08624 |
| 3 | attention_lstm | fit | 14855 | 20.1203 | 0.00378262 | 0.387186 | 0.546114 |
| 6 | persistence | calibration | 4951 | 24.0926 | -0.00595839 | 0.58778 | 0.79223 |
| 6 | persistence | test | 9907 | 28.9392 | -0.00206924 | 0.547946 | 0.781775 |
| 6 | persistence | fit | 14850 | 20.1198 | -0.00245118 | 0.558182 | 0.833365 |
| 6 | xgboost | calibration | 4951 | 24.0926 | -0.996619 | 1.21699 | 1.59299 |
| 6 | xgboost | test | 9907 | 28.9392 | -4.26907 | 4.27973 | 4.69144 |
| 6 | xgboost | fit | 14850 | 20.1198 | 0.000647766 | 0.440361 | 0.606999 |
| 6 | attention_lstm | calibration | 4951 | 24.0926 | -1.22531 | 1.40624 | 1.80109 |
| 6 | attention_lstm | test | 9907 | 28.9392 | -4.46156 | 4.46356 | 4.753 |
| 6 | attention_lstm | fit | 14850 | 20.1198 | -0.0508127 | 0.560737 | 0.755434 |

| horizon | role | origin_min | origin_max | minimum | maximum | mean | above_reference_max | below_reference_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | fit | 2021-01-08 00:00:00 | 2021-04-21 04:10:00 | 15 | 28.6 | 20.1205 | 0 | 0 |
| 1 | calibration | 2021-04-21 04:40:00 | 2021-05-25 14:00:00 | 17.5 | 29.6 | 24.0969 | 0.0109025 | 0 |
| 1 | test | 2021-05-25 14:20:00 | 2021-08-02 09:20:00 | 21.8 | 33.4 | 28.9392 | 0.617846 | 0 |
| 3 | fit | 2021-01-07 23:40:00 | 2021-04-21 03:20:00 | 15 | 28.6 | 20.1203 | 0 | 0 |
| 3 | calibration | 2021-04-21 04:10:00 | 2021-05-25 13:20:00 | 17.5 | 29.6 | 24.0953 | 0.0109047 | 0 |
| 3 | test | 2021-05-25 14:00:00 | 2021-08-02 09:00:00 | 21.8 | 33.4 | 28.9392 | 0.617846 | 0 |
| 6 | fit | 2021-01-07 23:10:00 | 2021-04-21 02:00:00 | 15 | 28.6 | 20.1198 | 0 | 0 |
| 6 | calibration | 2021-04-21 03:20:00 | 2021-05-25 12:20:00 | 17.5 | 29.6 | 24.0926 | 0.0109069 | 0 |
| 6 | test | 2021-05-25 13:30:00 | 2021-08-02 08:30:00 | 21.8 | 33.4 | 28.9392 | 0.617846 | 0 |

### rico

| horizon | model | role | n | truth_mean | bias | mae | rmse |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | persistence | calibration | 4452 | 26.6991 | 0.00799641 | 0.0875112 | 0.15265 |
| 5 | persistence | test | 8692 | 20.4079 | -0.0142315 | 0.0744708 | 0.12451 |
| 5 | persistence | fit | 12932 | 28.3236 | 0.00416796 | 0.112921 | 0.201201 |
| 5 | xgboost | calibration | 4452 | 26.6991 | 0.0115591 | 0.0741007 | 0.114717 |
| 5 | xgboost | test | 8692 | 20.4079 | 0.0804166 | 0.243495 | 0.411486 |
| 5 | xgboost | fit | 12932 | 28.3236 | 1.80054e-06 | 0.0263686 | 0.0344209 |
| 5 | attention_lstm | calibration | 4452 | 26.6991 | 0.112947 | 0.316716 | 0.39768 |
| 5 | attention_lstm | test | 8692 | 20.4079 | 1.89517 | 2.22306 | 2.70229 |
| 5 | attention_lstm | fit | 12932 | 28.3236 | -0.0134595 | 0.0845357 | 0.11171 |
| 15 | persistence | calibration | 4242 | 26.6903 | 0.025554 | 0.250778 | 0.407844 |
| 15 | persistence | test | 8282 | 20.4278 | -0.0390123 | 0.209382 | 0.33076 |
| 15 | persistence | fit | 12322 | 28.3186 | 0.0127901 | 0.320484 | 0.546724 |
| 15 | xgboost | calibration | 4242 | 26.6903 | 0.0648009 | 0.1769 | 0.281632 |
| 15 | xgboost | test | 8282 | 20.4278 | 0.197124 | 0.42446 | 0.616662 |
| 15 | xgboost | fit | 12322 | 28.3186 | 6.72616e-05 | 0.0312245 | 0.0411606 |
| 15 | attention_lstm | calibration | 4242 | 26.6903 | 0.128078 | 0.337267 | 0.416601 |
| 15 | attention_lstm | test | 8282 | 20.4278 | 2.08429 | 2.38261 | 2.86615 |
| 15 | attention_lstm | fit | 12322 | 28.3186 | 0.0136457 | 0.108207 | 0.145813 |
| 30 | persistence | calibration | 3927 | 26.6751 | 0.0541889 | 0.472116 | 0.725241 |
| 30 | persistence | test | 7667 | 20.4485 | -0.0674579 | 0.389696 | 0.599428 |
| 30 | persistence | fit | 11407 | 28.3109 | 0.0264048 | 0.596283 | 0.976333 |
| 30 | xgboost | calibration | 3927 | 26.6751 | 0.0688307 | 0.286695 | 0.461499 |
| 30 | xgboost | test | 7667 | 20.4485 | 0.27632 | 0.645699 | 0.905418 |
| 30 | xgboost | fit | 11407 | 28.3109 | 3.66871e-05 | 0.0346167 | 0.0464902 |
| 30 | attention_lstm | calibration | 3927 | 26.6751 | 0.0845705 | 0.364535 | 0.464826 |
| 30 | attention_lstm | test | 7667 | 20.4485 | 2.47531 | 2.64775 | 3.09428 |
| 30 | attention_lstm | fit | 11407 | 28.3109 | -0.0301915 | 0.102707 | 0.13981 |
| 60 | persistence | calibration | 3297 | 26.6433 | 0.114013 | 0.866758 | 1.23694 |
| 60 | persistence | test | 6437 | 20.4708 | -0.109492 | 0.715675 | 1.04138 |
| 60 | persistence | fit | 9577 | 28.2951 | 0.0565835 | 1.08858 | 1.66177 |
| 60 | xgboost | calibration | 3297 | 26.6433 | -0.18318 | 0.529087 | 0.864447 |
| 60 | xgboost | test | 6437 | 20.4708 | 0.583143 | 1.1955 | 1.78819 |
| 60 | xgboost | fit | 9577 | 28.2951 | 0.000209773 | 0.0979061 | 0.135823 |
| 60 | attention_lstm | calibration | 3297 | 26.6433 | 0.194406 | 0.444533 | 0.586934 |
| 60 | attention_lstm | test | 6437 | 20.4708 | 2.35347 | 2.63627 | 3.1144 |
| 60 | attention_lstm | fit | 9577 | 28.2951 | 0.0356327 | 0.18907 | 0.266368 |

| horizon | role | origin_min | origin_max | minimum | maximum | mean | above_reference_max | below_reference_min |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 | fit | 2023-07-26 15:24:00 | 2023-08-07 22:55:00 | 16 | 40.2 | 28.3236 | 0 | 0 |
| 5 | calibration | 2023-08-07 23:24:00 | 2023-08-12 02:55:00 | 18.9 | 35.6 | 26.6991 | 0 | 0 |
| 5 | test | 2023-08-12 07:24:00 | 2024-02-04 10:55:00 | 13.7 | 31 | 20.4079 | 0 | 0.107685 |
| 15 | fit | 2023-07-26 15:24:00 | 2023-08-07 22:45:00 | 16 | 40.2 | 28.3186 | 0 | 0 |
| 15 | calibration | 2023-08-07 23:24:00 | 2023-08-12 02:45:00 | 18.9 | 35.6 | 26.6903 | 0 | 0 |
| 15 | test | 2023-08-12 07:24:00 | 2024-02-04 10:45:00 | 13.7 | 31 | 20.4278 | 0 | 0.106979 |
| 30 | fit | 2023-07-26 15:24:00 | 2023-08-07 22:30:00 | 16 | 40.2 | 28.3109 | 0 | 0 |
| 30 | calibration | 2023-08-07 23:24:00 | 2023-08-12 02:30:00 | 18.9 | 35.6 | 26.6751 | 0 | 0 |
| 30 | test | 2023-08-12 07:24:00 | 2024-02-04 10:30:00 | 13.7 | 31 | 20.4485 | 0 | 0.108387 |
| 60 | fit | 2023-07-26 15:24:00 | 2023-08-07 22:00:00 | 16 | 40.2 | 28.2951 | 0 | 0 |
| 60 | calibration | 2023-08-07 23:24:00 | 2023-08-12 02:00:00 | 18.9 | 35.6 | 26.6433 | 0 | 0 |
| 60 | test | 2023-08-12 07:24:00 | 2024-02-04 10:00:00 | 13.7 | 31 | 20.4708 | 0 | 0.115892 |

[All candidate inner-validation errors](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/point_bias_by_role.csv) retain the original candidate IDs and selected choices. [RICO phase bias](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/rico_phase_bias.csv) distinguishes count-weighted metrics from equal-run diagnostics. Group RMSE reconciles through counts and squared errors, not an average of RMSE. Repeated runs, horizons and training seeds do not add independent acquisition periods.

## Why the frozen intervals miss

The radius is the declared finite-sample order statistic of that fitted model's calibration absolute errors. Test errors increase relative to this fixed radius. Coverage uses the saved inclusive lower/upper endpoints. Direct absolute-error comparisons can differ at floating-point boundary ties; both counts are exported and every difference is verified within floating-point precision. The first diagnostic attempt rejected these ties, and its failed log is preserved; the diagnostic was corrected without changing any model, interval or historical metric. Empirical test quantiles are retrospective descriptions only and never change a radius, candidate or threshold.

| dataset | horizon | model | frozen_radius | calibration_abs_q95 | test_abs_q95 | calibration_exceedance | test_exceedance | test_coverage |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rico | 5 | persistence | 0.3 | 0.3 | 0.3 | 0.0406559 | 0.0276116 | 0.972388 |
| rico | 5 | xgboost | 0.281252 | 0.280088 | 0.728714 | 0.0496406 | 0.265301 | 0.734699 |
| rico | 5 | attention_lstm | 0.753073 | 0.752914 | 4.97176 | 0.0496406 | 0.811896 | 0.188104 |
| bdg2 | 1 | persistence | 82.7 | 82.612 | 85.356 | 0.0499136 | 0.0532333 | 0.946767 |
| bdg2 | 1 | xgboost | 67.922 | 67.7946 | 69.2834 | 0.0499136 | 0.0521651 | 0.947835 |
| bdg2 | 1 | attention_lstm | 70.5194 | 70.5185 | 70.8721 | 0.0499136 | 0.0503753 | 0.949625 |
| pleia_energy | 1 | persistence | 0.0625 | 0.0625 | 0.59375 | 0.0421966 | 0.357121 | 0.642879 |
| pleia_energy | 1 | xgboost | 0.205216 | 0.204861 | 0.473138 | 0.0496669 | 0.197133 | 0.802867 |
| pleia_energy | 1 | attention_lstm | 0.0711639 | 0.0709702 | 0.465536 | 0.0496669 | 0.396891 | 0.603109 |
| pleia_energy | 3 | persistence | 0.0625 | 0.0625 | 0.585938 | 0.046042 | 0.360755 | 0.639245 |
| pleia_energy | 3 | xgboost | 0.130101 | 0.129999 | 0.489501 | 0.0496769 | 0.264056 | 0.735944 |
| pleia_energy | 3 | attention_lstm | 0.092966 | 0.0926737 | 0.498376 | 0.0496769 | 0.34087 | 0.65913 |
| pleia_energy | 6 | persistence | 0.0625 | 0.0625 | 0.601562 | 0.0452434 | 0.359342 | 0.640658 |
| pleia_energy | 6 | xgboost | 0.105165 | 0.105001 | 0.531523 | 0.0496869 | 0.315232 | 0.684768 |
| pleia_energy | 6 | attention_lstm | 0.119795 | 0.119753 | 0.528533 | 0.0496869 | 0.355102 | 0.644898 |
| rico | 15 | persistence | 0.8 | 0.8 | 0.7 | 0.0459689 | 0.0370683 | 0.962932 |
| rico | 15 | xgboost | 0.763905 | 0.763019 | 1.2546 | 0.0497407 | 0.18824 | 0.81176 |
| rico | 15 | attention_lstm | 0.776181 | 0.774549 | 5.27109 | 0.0497407 | 0.822024 | 0.177976 |
| rico | 30 | persistence | 1.5 | 1.5 | 1.3 | 0.0468551 | 0.035868 | 0.964132 |
| rico | 30 | xgboost | 1.20825 | 1.20789 | 2.12439 | 0.0496562 | 0.150515 | 0.849485 |
| rico | 30 | attention_lstm | 0.918014 | 0.917178 | 5.5435 | 0.0496562 | 0.864223 | 0.135777 |
| rico | 60 | persistence | 2.5 | 2.5 | 2.3 | 0.0494389 | 0.0391487 | 0.960851 |
| rico | 60 | xgboost | 1.93757 | 1.92586 | 3.20031 | 0.0494389 | 0.184403 | 0.815597 |
| rico | 60 | attention_lstm | 1.12911 | 1.12151 | 5.55095 | 0.0494389 | 0.796644 | 0.203356 |
| bdg2 | 3 | persistence | 172.1 | 172.1 | 177.5 | 0.0499424 | 0.0540127 | 0.945987 |
| bdg2 | 3 | xgboost | 100.754 | 100.754 | 100.709 | 0.0499424 | 0.0498845 | 0.950115 |
| bdg2 | 3 | attention_lstm | 118.027 | 118.027 | 118.45 | 0.0499424 | 0.0502309 | 0.949769 |
| bdg2 | 6 | persistence | 249 | 249 | 257 | 0.049683 | 0.0557737 | 0.944226 |
| bdg2 | 6 | xgboost | 124.376 | 124.371 | 124.702 | 0.0499135 | 0.0501732 | 0.949827 |
| bdg2 | 6 | attention_lstm | 138.171 | 138.072 | 139.138 | 0.0499135 | 0.0508372 | 0.949163 |
| pleia | 1 | persistence | 0.8 | 0.8 | 0.7 | 0.0482536 | 0.0348239 | 0.965176 |
| pleia | 1 | xgboost | 1.34442 | 1.34401 | 4.67299 | 0.0496669 | 0.665893 | 0.334107 |
| pleia | 1 | attention_lstm | 2.0962 | 2.09595 | 5.25549 | 0.0496669 | 0.723125 | 0.276875 |
| pleia | 3 | persistence | 1.2 | 1.2 | 1.2 | 0.0486672 | 0.0399717 | 0.960028 |
| pleia | 3 | xgboost | 2.35659 | 2.3543 | 6.21467 | 0.0496769 | 0.717069 | 0.282931 |
| pleia | 3 | attention_lstm | 2.65367 | 2.65335 | 6.14175 | 0.0496769 | 0.747249 | 0.252751 |
| pleia | 6 | persistence | 1.6 | 1.6 | 1.6 | 0.0476671 | 0.0469365 | 0.953063 |
| pleia | 6 | xgboost | 3.1517 | 3.15142 | 7.26655 | 0.0496869 | 0.68921 | 0.31079 |
| pleia | 6 | attention_lstm | 3.54216 | 3.54142 | 6.93417 | 0.0496869 | 0.725144 | 0.274856 |

[Both levels and full error distributions](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/frozen_radius_residual_shift.csv) and [calendar-month/original-group coverage](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/timeblock_group_coverage.csv) show heterogeneity hidden by pooled summaries. PLEIA energy preserves its zeros, stalls and catch-up values, including persistence failures. BDG2 is a contrasting pooled case on the same ten known buildings; near-nominal pooled coverage is not a conditional or unseen-building guarantee.

## Findings, hypotheses and preserved identity

Confirmed measurements: target/covariate range shifts, model-specific signed prediction bias, and changes between calibration and test absolute-error distributions. No new alignment, current-observation, channel-order, train-only scaling/inversion or saved-model identity defect is established. Existing independent checks resolve those correctness questions; this task additionally verifies raw support identity and saved final target scaling during inference. Architecture saturation, extrapolation behavior, training budget and loss/selection mismatch remain hypotheses, without controlled causal ablations. Neither a correlation nor another training seed establishes a repair.

The [older pilot diagnosis](PILOT_DIAGNOSTICS.md) used different fits and development partitions, and previously required 24 reproduced inner fits because those predictions had not been saved. This task performs zero fits and uses the current saved inner streams. Overlapping calendar dates do not make those old and current models identical. All source runs are byte-identical after diagnosis; [input manifest](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/input_manifest.csv) and [artifact identities](smart_building_conformal/outputs/matched_forecasting005/fold2_multiseed_batch_v1/diagnosis_v2/artifact_identity.csv) bind these conclusions. Scientific source SHA-256 remains `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`.
