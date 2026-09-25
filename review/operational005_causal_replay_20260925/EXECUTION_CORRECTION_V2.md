# Version-2 execution correction

The first v1 policy block completed with zero fits, but independent validation stopped before
zero-fit resume. The replay held adjacent floating-point values at an interval boundary: the
observed value was strictly below the issued lower bound in memory, while default CSV formatting
serialized both as `0.0007`. Across the six saved streams, all 884 discrepancies had the same
direction and boundary condition. The scientific replay flag was therefore internally correct;
the persisted decimal evidence was insufficient for exact independent reconstruction.

Version 1 remains untouched under `operational005_causal_replay_v1`. Version 2 writes the
observed value and both bounds with round-trippable decimal formatting and exact IEEE-754 hex
representations. The independent validator requires decimal/hex bit identity before recomputing
the flag. Focused guards cover this adjacent-float boundary and reject a tampered exact bound.

The same correction resolves an observability limitation discovered in v1: Windows virtual-
environment launchers introduce wrapper PIDs. Version 2 follows the verified child process tree
and records the actual Python worker identity and observed RSS without installing or upgrading
packages.
