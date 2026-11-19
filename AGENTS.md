## Shared Blue delivery guidance

For implementation, fixes and independent review, use the installed `blue-delivery`
skill: Codex `~/.agents/skills/blue-delivery/SKILL.md`, Claude Code
`~/.claude/skills/blue-delivery/SKILL.md`. It covers task authority, cross-repository
boundaries, checkpoints, evidence and review; simple factual questions need no workflow.
Harness profile: `blue-packages`. The selected immutable release contains
`skills/blue-delivery/references/repos/blue-packages.md`; load only relevant deeper references.
Reuse the task's recorded release on resume; new tasks resolve the workstation's reviewed
release through the shared entry. Keep the pin in ignored task artifacts, not product config.
If the skill is missing, report it and direct the engineer to the
[team harness README](https://github.com/bluecontract/dev-agents-harness/blob/main/README.md)
for one-time installation; do not claim the harness was followed or create a repo payload copy.
Existing critical repository rules and user authorization remain in force.
