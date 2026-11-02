# Does a forecast alert arrive after the injected disturbance has cleared?

Analysis design fixed locally before inspecting outcomes for this endpoint on either cohort. The original pilot's aggregate outcomes had already been examined. This is an exploratory study and a site-disjoint BDG2 replication within the same dataset.

## One primary comparison

For the separate-tail CQR numerical detector at a validation workload budget of 0.5 episode per meter-day, count all originally credited event hits. Within those hits count first episode onsets strictly after the last actually altered reading where the meter value has returned to its original value and removing only this event would turn the current numerical flag off. Divide this count by all credited hits. Report counts, site variation and a site-balanced sensitivity. This fraction is about timing and attribution of credited detections. Actual operator usefulness depends on the action and is outside the experiment.

Each paired replay keeps the fitted forecaster, preselected policy, weather, unmodified measurements and all earlier injected events the same. Restore only this event's altered readings in the comparison replay. Recompute the forecast from its history. Reproduce factual alerts against the audited packed stream. Distinguish changed flags from episode boundaries changing while the current flag persists. Record pre-change matches, first matches during the disturbance span, matches after its last changed sample, after the nominal four-hour injection slot, and no hit. A within-span match is temporal coincidence unless separately attributed. A later match can still be valuable for retrospective fault logging.

Report all four policies at the three original budgets, numerical and combined channels, families, buildings and periods. Also report the proportion on an all-effective-event denominator. Count one fitting seed, 42, and five event placements per period. Repeated fitting seeds produced identical clean forecasts in the pilot. Use event counts as descriptive replay counts. Do not infer that injections are independent real faults.

## Replication before examining new results

Select one electricity meter per eligible BDG2 site outside the ten-building pilot's six sites. Choose the lexicographically first eligible building ID at each site. Use only the first 35% of global hourly timestamps to screen for at least 95% finite readings, positive variation and at most 50% adjacent equal readings. Exclude sites without an eligible meter. Freeze membership before fitting. Use the original shared HGB model and protocol in the new cohort, one fitting seed, all three periods and five injection catalogues. This tests another group of meters with the same source and injector. It does not test transfer of model weights or independently documented equipment faults.

As an editorial decision rule, prioritize the mechanism if at least 10% of the primary detector's credited hits satisfy the strict history-only condition in each cohort and the effect occurs at a majority of observed sites in each. This threshold is a research-prioritization choice. Report smaller effects and all sensitivity results regardless. A measured effect alone cannot establish priority over prior work.

Input is the original BDG2 raw-file triple and the audited pilot artifacts. Refit only the site-disjoint cohort. The comparison replay uses privileged original measurements and is available offline for attribution. Deployment-time correction would need a separate algorithm and prospective evaluation.
