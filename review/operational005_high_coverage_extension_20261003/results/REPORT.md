# Operational005 high-coverage extension: BDG2 one-hour CQR and uncalibrated quantiles

Descriptive results of the separately versioned extension. They are not part of the candidature
report, and they do not change the accepted operational005 tables, figures or captions.

- 99 previously unavailable candidates (90 CQR, 9 uncalibrated quantile) at nominal
  0.975, 0.99 and 0.995, over three outer folds and five model seeds:
  1,485 evaluation rows in 495 policy blocks.
- 45 new CQR owners (135 quantile-estimator fits, 90 conformalize operations), one per unit and level,
  shared by the CQR and uncalibrated-quantile candidates. No forecasting model was refitted.
- Every block passed the frozen validator and an extended independent validator (maximum absolute difference 4.55e-13) and resumed without change.
- Combined with the 165 accepted candidates: 264 candidates and 3,960 evaluation rows. Native and common support are two views of the
  same evaluations, not additional experiments.

Folds, model seeds, catalogue seeds and support views are not independent population replicates, so no
confidence interval or significance claim is made, and no setting is selected from these test outcomes.

## Native-support means by method, nominal level and recalibration strategy

Each row averages the candidates' fold/seed means over the three temporal rules (single sample, 3 of 3
in 180 min, 4 of 6 in 360 min). Source: extension = completed here; original = accepted operational005 tables.

| Method | Level | Strategy | Source | Candidates | Macro recall | Micro recall | Custom F1 | Episode precision | Clean episodes per asset-day | Restricted detection (min) |
|---|---:|---|---|---:|---:|---:|---:|---:|---:|---:|
| cqr | 0.95 | periodic | original | 9 | 0.363 | 0.369 | 0.268 | 0.545 | 0.386 | 262.9 |
| cqr | 0.975 | periodic | extension | 9 | 0.316 | 0.320 | 0.271 | 0.698 | 0.199 | 273.6 |
| cqr | 0.99 | periodic | extension | 9 | 0.259 | 0.259 | 0.261 | 0.826 | 0.078 | 287.6 |
| cqr | 0.995 | periodic | extension | 9 | 0.227 | 0.225 | 0.244 | 0.887 | 0.044 | 296.5 |
| cqr | 0.95 | rolling | original | 18 | 0.348 | 0.353 | 0.274 | 0.598 | 0.355 | 266.2 |
| cqr | 0.975 | rolling | extension | 18 | 0.292 | 0.294 | 0.269 | 0.736 | 0.182 | 279.6 |
| cqr | 0.99 | rolling | extension | 18 | 0.228 | 0.226 | 0.239 | 0.847 | 0.076 | 296.4 |
| cqr | 0.995 | rolling | extension | 18 | 0.191 | 0.186 | 0.210 | 0.887 | 0.045 | 307.3 |
| cqr | 0.95 | static | original | 3 | 0.364 | 0.369 | 0.258 | 0.569 | 0.396 | 262.0 |
| cqr | 0.975 | static | extension | 3 | 0.314 | 0.317 | 0.254 | 0.662 | 0.205 | 274.1 |
| cqr | 0.99 | static | extension | 3 | 0.257 | 0.257 | 0.243 | 0.768 | 0.084 | 288.5 |
| cqr | 0.995 | static | extension | 3 | 0.235 | 0.233 | 0.244 | 0.819 | 0.043 | 294.8 |
| quantile_uncalibrated | 0.95 | static | original | 3 | 0.385 | 0.391 | 0.259 | 0.403 | 0.553 | 260.5 |
| quantile_uncalibrated | 0.975 | static | extension | 3 | 0.353 | 0.358 | 0.259 | 0.466 | 0.375 | 267.0 |
| quantile_uncalibrated | 0.99 | static | extension | 3 | 0.324 | 0.327 | 0.280 | 0.608 | 0.194 | 273.5 |
| quantile_uncalibrated | 0.995 | static | extension | 3 | 0.280 | 0.281 | 0.263 | 0.573 | 0.137 | 284.2 |
| recentred_enbpi | 0.95 | native_updated | original | 3 | 0.375 | 0.381 | 0.302 | 0.568 | 0.344 | 263.3 |
| recentred_enbpi | 0.975 | native_updated | original | 3 | 0.318 | 0.320 | 0.288 | 0.659 | 0.187 | 276.4 |
| recentred_enbpi | 0.99 | native_updated | original | 3 | 0.254 | 0.253 | 0.257 | 0.781 | 0.082 | 291.6 |
| recentred_enbpi | 0.995 | native_updated | original | 3 | 0.210 | 0.207 | 0.223 | 0.860 | 0.042 | 302.7 |
| recentred_enbpi | 0.95 | periodic | original | 9 | 0.375 | 0.381 | 0.303 | 0.568 | 0.344 | 263.3 |
| recentred_enbpi | 0.975 | periodic | original | 9 | 0.318 | 0.321 | 0.288 | 0.654 | 0.187 | 276.4 |
| recentred_enbpi | 0.99 | periodic | original | 9 | 0.256 | 0.255 | 0.259 | 0.776 | 0.083 | 291.3 |
| recentred_enbpi | 0.995 | periodic | original | 9 | 0.212 | 0.209 | 0.227 | 0.856 | 0.043 | 302.3 |
| recentred_enbpi | 0.95 | rolling | original | 18 | 0.345 | 0.350 | 0.300 | 0.621 | 0.312 | 271.1 |
| recentred_enbpi | 0.975 | rolling | original | 18 | 0.277 | 0.278 | 0.273 | 0.712 | 0.153 | 286.6 |
| recentred_enbpi | 0.99 | rolling | original | 18 | 0.214 | 0.212 | 0.230 | 0.801 | 0.069 | 302.5 |
| recentred_enbpi | 0.995 | rolling | original | 18 | 0.190 | 0.186 | 0.203 | 0.845 | 0.036 | 309.0 |
| recentred_enbpi | 0.95 | static | original | 3 | 0.334 | 0.337 | 0.275 | 0.500 | 0.332 | 274.7 |
| recentred_enbpi | 0.975 | static | original | 3 | 0.277 | 0.277 | 0.249 | 0.624 | 0.176 | 288.1 |
| recentred_enbpi | 0.99 | static | original | 3 | 0.225 | 0.223 | 0.220 | 0.737 | 0.079 | 300.2 |
| recentred_enbpi | 0.995 | static | original | 3 | 0.203 | 0.199 | 0.208 | 0.806 | 0.041 | 305.6 |

Rows held at the previous correction because a scheduled update lacked score or rank support (all streams, all folds and seeds): none.

Original rows (every recentred EnbPI row, and the 0.95 CQR and uncalibrated-quantile rows) are recomputed from the accepted operational005 metric table read from its committed blob. Extension rows are the 0.975, 0.99 and 0.995 CQR and uncalibrated-quantile candidates completed here.
