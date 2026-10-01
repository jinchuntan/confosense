# Publication credential-gate correction v1.3

The v1.2 publication attempt stopped before staging because the credential
scanner inspected `completion_delivery_v1.py`, whose own source contained the
literal byte signatures it was designed to reject. No other allowlisted file
was flagged, and neither the local nor remote publication branch moved.

Version 1.3 constructs those same detection signatures from byte fragments, so
the scanner source does not match itself. Detection scope and rejection
signatures are otherwise unchanged. The correction also identity-checks and
reuses the already-passed completion-validation and external-backup receipts;
it does not repeat experiments, validation, aggregation, or archive creation.

The v1.2 failure remains preserved in
`PUBLICATION_CREDENTIAL_GATE_FAILURE_V1_2.json`.
