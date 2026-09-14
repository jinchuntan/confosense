# Interval failure diagnostic

The read-only extension covers all 130 preserved seed-42 method cells. The native CQR score/correction calculations reconstruct; no new arithmetic or owner-identity defect was demonstrated. Existing independent saved-owner validation remains authoritative for the native EnbPI OOB convention and dtype. Source artifacts remain byte-identical.

| horizon | method | native_coverage | calibration_bias_prediction_minus_y | test_bias_prediction_minus_y | calibration_abs_error_q95 | test_abs_error_q95 | below_fraction | above_fraction |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | cqr | 0.311901 | -0.385323 | -3.14792 | 1.76259 | 5.78044 | 0.00151408 | 0.686585 |
| 1 | recentred_enbpi_static | 0.0879176 | -0.569387 | -3.14597 | 1.9553 | 5.82668 | 0.0013122 | 0.91077 |
| 3 | cqr | 0.336025 | -0.763658 | -4.02893 | 2.81604 | 6.94206 | 0 | 0.663975 |
| 3 | recentred_enbpi_static | 0.0565257 | -0.982716 | -4.37527 | 3.09435 | 7.28398 | 0.000605632 | 0.942869 |
| 6 | cqr | 0.373776 | -1.11248 | -4.80957 | 3.64114 | 7.69634 | 0 | 0.626224 |
| 6 | recentred_enbpi_static | 0.0554154 | -1.18161 | -4.7132 | 3.63545 | 7.7611 | 0.000201877 | 0.944383 |

Static EnbPI uses native OOB calibration scores, while its centre is the preserved full-fit predictor. Those native scores can be far narrower than errors of that fixed predictor on the calibration and later test periods. The frozen MAPIE conformalization includes its declared calibration bootstrap fits; it is not equivalent to fixed-model absolute-error calibration. Nonfinite OOB scores remain counted explicitly. Undercoverage therefore cannot be explained away by swapping to another owner or treating every calibration score as the fixed predictor residual.

11 of 26 CQR level/horizon rows contain a negative native tail correction. Negative valid scores shrink overly wide raw tails under the declared convention. Levels are fitted separately and need not nest. For PLEIA-energy h1, the 95% upper correction is -0.24914174650502302. It is retained, with its resulting undercoverage.

Observed facts are the own-predictor bias, signed error distribution shifts, miss directions and support differences in the CSVs. Distribution change and the native OOB-versus-fixed-predictor calibration construction explain the numerical discrepancy descriptively. A unique causal attribution to meter faults, architecture, extrapolation or a particular covariate is unproven. No clipping, widening, row removal, level/rank changes or retuning occurred. No completed pilot is invalidated by this package.

[All-method table](../../smart_building_conformal/outputs/conditional_context005/interval_diagnostic_extension_v1/all_method_diagnostic.csv), [owner scores/corrections](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/interval_owner_diagnostic.csv), [score distributions](../../smart_building_conformal/outputs/conditional_context005/implementation_support_v1/score_distributions.csv).
