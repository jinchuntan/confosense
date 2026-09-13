# Authorized BDG2 operational pilot

This review branch descends from `2243c167804690ad1ec9b8aebc369e5596d392aa`. The complete handoff is `5cb65680bf4ab680db1be607bcd1ec5a6c8d0b5b:review/NEXT_TASK_BDG2_OPERATIONAL_PILOT.md`; its older underlying implementation was not checked out.

One unit is authorized: BDG2, outer fold 2, model seed 42, primary horizon 1 hour, all ten retained buildings, catalogue seeds 42–46, and the nine exact candidates in [the original proposal](../amendment004_20260913/next_bounded_proposal.json). The frozen configuration, events, membership, thresholds and estimators are unchanged. Full-study execution is not authorized by this run.

Execution-only additions record the durable logger's process IDs/start state, pre-fit membership/data/configuration/proposal checks, exact source ZIP, phase memory/time and outer paired bootstrap draws. The existing scientific engine calls retain their arguments and ordering; an optional observer encloses each inner and outer phase. The journal binds this invocation to the specifically authorized BDG2 proposal. Historical run identities remain historical; the new unit has its own identity and directory.

The entrypoint still requires 3 GiB available physical RAM before preparation. Numerical thread controls are set to one, and real model fitting is sequential. No interval, recall, workload or event setting is adjusted after outcomes become visible.

Completion and validation evidence will be indexed separately here after the command exits. A completed checkpoint permits zero-fit resume; partial-stage recovery is not claimed.
