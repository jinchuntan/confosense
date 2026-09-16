# Raw-package recovery record

The original `final/package_raw` attempt `2026-09-16T191637068502+0000_ba1d4088` exited 1 after 1,562.536 seconds. Its receipt and command log identify `AttributeError: 'function' object has no attribute 'DictWriter'`: the `csv` helper imported from `common` shadowed the standard-library `csv` module during metadata creation.

The seed-43 core archive and all nine bounded context archive parts were already written. The repair uses an explicit `csv_module` alias, validates existing ZIP member paths and hashes against the immutable scientific `COMPLETE.json` tree, retains incomplete manifest metadata with a dated failure suffix, and writes only missing metadata. The recovery gate accepts only this exact failed receipt, error string, command identity, and retained seed-43 partial archive root.

A first reuse attempt then exited before writing any new archive because the recovery path used `dest.mkdir(parents=True)` rather than `exist_ok=True`. The exact receipt records `FileExistsError [WinError 183]`; the 11 preserved seed-43 artifacts were unchanged. The path now permits the existing verified directory and the recovery gate admits only that additional exact error signature.

A second reuse attempt exposed that valid archive parts include `COMPLETE.json`, which is intentionally outside that file's internal `files` map. Verification now hashes that manifest directly; a regression test covers creating and reusing an archive containing both a scientific payload and `COMPLETE.json`.
