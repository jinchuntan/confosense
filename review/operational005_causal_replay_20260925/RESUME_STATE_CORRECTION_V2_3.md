# Resume-state correction 2.3

The v2 block and its revision-2.2 independent validation remain unchanged. Before relaunch, the
coordinator and supervisor were found to merge new live state into their prior blocked JSON files
without clearing the old `exact_error`, exit code, and finish timestamp. The underlying failed
states are already preserved by the versioned failure receipts and predecessor protocols.

Revision 2.3 clears only those stale live-state fields when a verified resume begins. It does not
change replay, conformalization, alert, metric, owner, queue, validation, or fit behavior.
