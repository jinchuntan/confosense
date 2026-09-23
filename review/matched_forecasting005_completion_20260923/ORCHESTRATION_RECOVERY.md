# Investigated unit-check recovery

The coordinator stopped after the accepted scientific `run`, existing-validator `validate`, and completed zero-fit `resume` phases for `pleia_energy_h1_f0_s43_v1`. The failed orchestration-only comparison is preserved as attempt `2026-09-23T055900469394+0000_23e1f57f`; its command-log SHA-256 is `697c36c756b8898c7aea6f45338a015b230bd632fe208bd2e4122dd2a026188e`.

The only mismatch was the serialized spelling of an absent `group_id`: the historical persistence owner used an empty string and the current run used the literal string `None`. Row IDs, target times, outcomes, persistence predictions, residuals, interval levels and interval bounds compared exactly. The run journal contains exactly eight completed tuning fits and two completed final fits, the existing validator passed, and the completed resume fitted zero models without changing run files.

The recovery normalizes those two absent-value spellings only inside the orchestration persistence-alias comparison. It authorizes one rerun of the failed zero-fit `unit_check`; the passed scientific run, validation and resume tasks must be reused and cannot be repeated by this recovery path. A different failed task, attempt identity or log hash remains a blocker.

## Cumulative-analysis retry

After all 125 new units were accepted, the first zero-fit cumulative-analysis attempt stopped before writing a result file. The failure is preserved as attempt `2026-09-23T164031180513+0000_641174df`; its command-log SHA-256 is `b32480cd457013dc77bc877b903dbcb867283abc85d1ce9ae388d306a6c4b7ed`.

The 210 historical point-cell rows already carried four derived signed/absolute coverage-deviation columns, while the 375 newly summarized rows correctly supplied the underlying achieved-coverage values but not those later-derived columns. Concatenating the two schemas therefore introduced temporary missing values before the inherited helper could recompute the columns. The recovery drops only the stale derived columns and recomputes them uniformly from achieved coverage for all 585 point cells. It permits one exact zero-fit analysis retry only after reconciling 125 accepted units, 1,000 tuning fits and 250 final fits; a nonempty partial analysis destination or a different failure identity remains a blocker.
