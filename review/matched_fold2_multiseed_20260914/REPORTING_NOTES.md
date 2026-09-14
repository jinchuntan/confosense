# Reporting-only corrections after the evaluated pre-fit commit

The evidence index's initial recomputation example placed its output outside the repository. `analyze.reports` and figure provenance use `out.relative_to(ROOT)`, so that example would fail when creating source links. The publisher now gives an absolute path beneath the repository, resolved from the repository working directory, and accurately states that saved execution manifests retain the original absolute layout.

This changes only the generated documentation string in `publish.py`. No scientific source, fitted object, candidate, interval, metric, frozen manifest, training command or running worker changed. The evaluated scientific digest remains `cd907183301a189ddfcc195774dad58c8fa07d5b326d2ac29cf3636383dc681e`. The original evaluated helper identity remains in `evaluated_commit.json`; later publication commits preserve this documentation correction separately in their history.
