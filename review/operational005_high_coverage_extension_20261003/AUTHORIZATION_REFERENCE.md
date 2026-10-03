# Authorization reference: operational005 high-coverage extension

Source: explicit instruction from Nigel in the Claude Code session of 2026-10-03, given after the
Chapter 4 figure package was published (branch `review/chapter4-figures-20261003`, commits
`9cd2885f50` and `635fc3fdc7`).

Authorised scope, quoted from the instruction:

- "Complete only the previously unavailable BDG2 one hour configurations for CQR and uncalibrated
  quantiles at nominal coverage levels 0.975, 0.99 and 0.995."
- "I explicitly authorise the additional model fitting and conformal calibration required for this
  extension."
- "Fit missing models using the established quantile model specification and original chronological
  roles. Share the appropriate fitted model between uncalibrated quantile and CQR evaluations. Do not
  substitute 95% quantile predictions for higher coverage quantiles."
- "Do not rerun the 825 accepted blocks or their 2,475 evaluation rows."
- "The old zero-fit restriction continues to describe the historical delivered replay. It does not
  prohibit the newly authorised fitting in this separate extension."
- "Do not use test outcomes to select new settings or claim population significance."
- "These results will remain separate from my candidature report."

Constraints carried into the extension protocol: preserve `main`, the candidature evidence package,
all accepted scientific outputs, the figure branch and its working folder, and the frozen tag
`candidature-evidence-20261002-v1` at `d65147ff22e6c079603eda1337630254796c8990`; do not edit
historical protocols, availability records or validation guards; do not refit unrelated forecasting
or interval models; publish to the extension branch only.
