# Operational005 delivery-validator correction v1.1

The first delivery-only validation attempt stopped after reconstructing all 825 accepted blocks. The reconstructed raw metric frame had 41 scientific columns, while the aggregate output had those same columns plus the intentional provenance column `status` written by the frozen `aggregate.py` implementation.

Version 1.1 requires the published schema to equal the raw schema plus exactly `status`, requires every status value to equal `validated`, and compares all 41 reconstructed scientific columns without changing tolerances. The original failure record and runtime events are preserved. This correction does not change replay evidence, aggregation, scientific definitions, validation receipts, zero-fit resumes, or results.
