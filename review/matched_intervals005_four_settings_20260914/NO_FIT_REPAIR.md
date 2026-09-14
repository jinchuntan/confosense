# Preserved no-fit repair

The first PLEIA-energy freeze attempt stopped before fitting an interval owner. Its fresh joint-origin counts were exactly 14,845 fit, 4,943 calibration, and 9,902 test, but all membership keys differed bytewise because a native single-series group identifier was `None` while the published CSV represented that same identifier as an empty field.

The repair canonicalizes only null single-series group identifiers to the published empty representation before joint membership comparison. Named BDG2 and RICO identifiers are unchanged. The bounded 27-test suite then passed, including explicit ten-minute and one-minute joins plus a RICO run-gap causal-replay check. The failed no-fit coordinator records are retained under `smart_building_conformal/outputs/matched_intervals005/four_settings_f2_s42_v1_coordinator`; the corrected PLEIA-energy protocol uses `v2` so the rejected attempt remains auditable.

The coordinator’s first process also exposed a missing durable-engine journal import after it had launched the PLEIA-energy worker. The exact worker identity was adopted by the repaired coordinator; no duplicate fit was launched. The original progress record retains this incident and the completed worker’s logger receipt records its actual exit.
