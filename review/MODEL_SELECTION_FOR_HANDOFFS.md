# Model recommendation for future ConfoSense handoffs

User preference recorded 14 September 2026: include the recommended Codex model and reasoning effort with every new handoff prompt. Avoid defaulting every task to Astra / Extra High.

Working recommendations, to be reconsidered against the actual task:
- Sol / Medium: status checks, existing-script execution, straightforward report or figure updates.
- Sol / High: bounded extensions of validated implementations, checkpoint orchestration, regression debugging and matched batch execution.
- Astra / Extra High: unresolved research-design questions, leakage/causality problems, major methodology architecture and difficult statistical interpretation.

These are task-specific judgments, not a guarantee that a model will succeed or be cheapest. A multi-hour numerical run alone does not require a stronger reasoning model. Changing the assistant model must not change scientific settings or weaken validation.

For the four-seed BDG2 interval extension: Sol / High. The method implementation and validation exist; the work extends seed-aware scope and reuse, then executes a fixed batch. Escalate only when a concrete unresolved problem calls for deeper analysis; do not interrupt ordinary execution merely to request a model upgrade.

User authorization to publish relevant artifacts on non-main review branches continues. Main and historical evidence remain preserved.
