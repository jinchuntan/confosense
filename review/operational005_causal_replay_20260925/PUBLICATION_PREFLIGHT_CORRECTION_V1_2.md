# Operational005 publication-preflight correction v1.2

Delivery v1.1 completed scientific validation and the byte-verified external backup, then stopped before staging because the explicit allowlist loop required `PREPUBLICATION_MANIFEST.json` to exist before that same loop created it.

Version 1.2 excludes only that self-describing manifest from the pre-creation hash loop, creates it from the other explicit allowlist members, and then stages the complete explicit list. The watcher also treats a child that exits between polling and identity inspection as exited rather than as an identity mismatch. The original failures remain preserved. No scientific artifact, aggregate, validation tolerance, Git branch, or remote ref was changed by the failed attempt.
