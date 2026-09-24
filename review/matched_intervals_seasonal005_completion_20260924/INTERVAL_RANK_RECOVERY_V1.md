# Interval-rank recovery v1

Cause: the frozen independent validator used ordinary `1-level` arithmetic,
while MAPIE 1.4.1 derives alpha through `Decimal` and applies its affine
reversed-probability expression.  For seed 46, horizon 1, level 0.9, this
crossed one order-statistic rank on each bound.  The lower residual changed by
`-0.023950805664043173`, exactly explaining the reported lower-bound offset.

The separately versioned external correction preserves the frozen scientific
source, package versions, outputs, failed attempt, tolerances, and protocol.
Full corrected validation passed all 30 method cells.  The seed-46 forbidden-fit
resume verified 138 stages with no file changes.  The four earlier bundles
passed 48 affected bound cells over
1652224 row/bound comparisons.  Focused tests: 8 passed.

Operation counts remain exactly equal to the frozen protocol and
`operations.jsonl` remains `ede89b6dc39d6573de8670573692e9acec164157722ad570426bd13c6c552085`.
