# Committed-blob manifest correction

The initial `EVIDENCE_MANIFEST.csv` was generated from local working-tree bytes. Four Markdown/JSON entries reflect the repository's CRLF checkout representation rather than the LF committed blob representation. The contents normalize identically; this is a packaging/line-ending issue, not a scientific or validator result.

`COMMITTED_BLOB_MANIFEST_V2.csv` therefore records SHA-256 and byte counts read directly from Git blobs at the earlier delivery-receipt commit `47595bfd7081f125e1f65a01971d5a82b2d2c40c`. Its companion receipt explicitly does not claim to verify the later correction commit that contains it.

The accepted pilot, frozen source, protocols, validator result, backup, and primary GitHub HTTPS readback are unchanged.
