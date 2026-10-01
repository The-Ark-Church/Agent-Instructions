# Agent-Instructions — The Ark Church AI Knowledge Base

The home base for AI at The Ark Church. This repo holds everything an AI assistant needs to know about who The Ark is, how we communicate, and what our brand looks like — plus skills for staff.

**No secrets, tokens, or passwords are stored in this repo** — credentials always stay on your own machine.

## For AI agents

Read these first, in this order:

1. [`knowledge-base/ark-org-profile.md`](knowledge-base/ark-org-profile.md) — who The Ark is
2. [`knowledge-base/ark-brand-kit.json`](knowledge-base/ark-brand-kit.json) — all structured brand data (colors, fonts, logos, voice)
3. [`knowledge-base/ark-communications-style-guide.md`](knowledge-base/ark-communications-style-guide.md) — writing rules; apply them automatically
4. [`knowledge-base/ark-terminology.md`](knowledge-base/ark-terminology.md) — correct names for ministries, rooms, and programs

## Contents

| Folder | What's in it |
|---|---|
| [`knowledge-base/`](knowledge-base/) | Org profile, brand kit, style guide, terminology, brand review page, and all brand assets (logos, elements, vector sources) |
| [`org-instructions/`](org-instructions/) | Claude Teams org-level instructions and profile (source of truth for what's pasted into the admin console) |
| [`skills/`](skills/) | Skills staff can install for their assistant |
| [`recipes/`](recipes/) | Ready-to-deploy recipes for other systems — e.g. a [Workflow Health dashboard](recipes/workflow-health-dashboard/) for Rock RMS |

## Connecting tools

| Tool | How staff connect it |
|---|---|
| **Basecamp** | In the Claude desktop app, open the **Code** tab and say **"set up Basecamp."** The [`set-up-basecamp`](skills/set-up-basecamp/) skill installs 37signals' official Basecamp CLI (no admin rights needed), signs you in, and connects Basecamp to Claude. Afterward it works in Code, regular chat, and Cowork. |

## For humans

- **Brand at a glance:** [`knowledge-base/ark-brand-review.html`](knowledge-base/ark-brand-review.html) (also published at thearkchurch.com/brand)
- **Brand guide PDF:** [`knowledge-base/assets/The-Ark-Church-Brand-2025.pdf`](knowledge-base/assets/The-Ark-Church-Brand-2025.pdf)
- **Getting started with AI at The Ark:** see thearkchurch.com/ai

## Contributing

Staff with repo access can propose changes by pull request. Questions or requests: contact Jonathan (IT).
