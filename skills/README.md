# Skills

Skills The Ark Church staff can install for their AI assistant.

| Skill | Status | Purpose |
|---|---|---|
| [`ark-writing-coach`](ark-writing-coach/) | ✅ Available | Polishes drafts to Ark Communications Style Guide standards automatically |
| [`build-my-style-guide`](build-my-style-guide/) | ✅ Available | Run-once writing interview (8 church-staff prompts) that produces a personal style guide for ghostwriting |
| [`write-like-me`](write-like-me/) | ✅ Available | Ghostwrites in your personal voice, with the Ark style guide always applied on top |
| [`action-method`](action-method/) | ✅ Available | Coaches proposals, decision requests, and upward communication into rigorous structure (Wes Kao's framework) |
| [`ark-brand`](ark-brand/) | ✅ Available | Produces Ark-branded PDFs and documents automatically — Ark palette, Smile Logo, Montserrat — when no styling is specified; pairs with `ark-writing-coach` (words vs. look) |

## How staff get skills

- **claude.ai / Claude Desktop (most staff):** an admin uploads the skill (zip of its folder) in the Claude Teams admin console — it becomes available org-wide, nothing to install.
- **Claude Code:** copy the skill folder into `~/.claude/skills/`.

Skill `reference/` files — and, for `ark-brand`, the bundled `assets/` logos and fonts — are copies of the `knowledge-base/` documents. Update the knowledge base first, then refresh the copies and re-upload.
