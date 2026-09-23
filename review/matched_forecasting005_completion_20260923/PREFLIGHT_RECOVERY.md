# Pre-fit authorization-path recovery

The first freeze command for `pleia_energy_h1_f1_s42_v1` exited 1 before writing a protocol or invoking any fit. The unchanged authorization had been placed under `review/`, while the existing runner requires every hashed input to be beneath `smart_building_conformal/`.

The failed command receipt and its partially written membership/boundary files are preserved under the original `preflight/` log and protocol path. No file was deleted or overwritten. The authoritative identical authorization is now versioned under `smart_building_conformal/configs/`; all final designs use the new `_core_completion_v1` protocol namespace and `preflight_v2` receipts.
