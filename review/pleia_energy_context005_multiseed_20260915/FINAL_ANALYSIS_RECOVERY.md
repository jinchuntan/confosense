# Final analysis recovery record

The original `final/analyze` attempt `2026-09-16T182952779570+0000_0dc6b9d1` exited 1 after 240.883 seconds. Its immutable receipt and command log identify `KeyError: 'control_id'` at the merge of macro and inference bounds.

All 421,800 saved original-context contributions have a nullable `group_id`. `macro_from_contributions` used pandas' default `dropna=True`, silently removed all contributions, then produced an empty macro frame. The repair sets `dropna=False` only for that provenance grouping. A real saved-evidence no-fit check now yields 84,360 seed/context averages, 1,260 stratum rows, and 60 control/rule/channel macro cells.

The failed analysis output directory was empty. The coordinator recovery gate verifies the exact failed task, logger receipt, `KeyError`, and empty output before retaining that directory under a dated failure path and permitting one new analysis attempt. It does not re-run any scientific unit or change `src`.
