---
name: write-like-me
description: Ghostwrite communications in an Ark staff member's personal voice, polished to Ark Church standards. Use when someone wants original writing they'll sign their name to — congregation emails, announcements, volunteer messages, social posts, staff memos — and says "write this for me," "draft this in my voice," "make it sound like me," or "ghostwrite this." Requires a personal style guide from the build-my-style-guide skill; if none exists, suggest running that first. For light editing of existing text, use ark-writing-coach instead.
---

# Write Like Me

<!-- Adapted for The Ark Church from Triumph Tech's rock-claude-plugins (Apache 2.0). -->

Drafts communications that sound like the author wrote them, then polishes against The Ark's standards — without stripping what makes the author's writing distinctive.

**Three layers, in order of precedence:**

1. **Ark Communications Style Guide** ([reference/ark-style-rules.md](reference/ark-style-rules.md)) — always wins. Times, dates, ministry names, external emoji list, religious capitalization: non-negotiable regardless of personal style.
2. **The author's personal style guide** — voice, rhythm, greetings, warmth, sign-offs. Protects the author's patterns from generic "polish."
3. **General writing quality** — applied last, and only where the two guides above are silent.

## Phase 1: Find and read the personal style guide

Look for it before asking anything:
- **Claude Code:** `context/style-guide.md` in the workspace
- **claude.ai:** a "[Name]'s Writing Style Guide" document in the project, or ask the author to paste it

If there's no style guide, stop and suggest running **build-my-style-guide** first (about 10 minutes). Don't draft without it.

Read it fully and build two lists:
- **Voice-protected patterns** — softeners, recurring phrases, greeting/sign-off habits, how they deliver hard news, sentence rhythm. These survive the polish pass.
- **Structural preferences** — length, paragraph density, punctuation habits.

## Phase 2: Gather framing

Four questions (one AskUserQuestion call where available; otherwise conversationally). Pre-fill anything already answered in their request:

1. **What is this?** — congregation email, announcement, volunteer message, social post, staff memo, pastoral note…
2. **Who's the audience?** — the whole congregation, a serve team, staff, one person, the public
3. **What are the main points?** — brain-dump welcome
4. **What should the reader do or feel afterward?** — sign up, show up, feel cared for, say yes, be informed

Question 4 drives every structural choice. If they stated a goal in their request, confirm it back ("I'm treating [X] as the goal — right?") rather than inferring silently.

## Phase 3: Draft in their voice

Write it. The personal style guide is calibration, not a checklist — the goal is what the author sounds like on a normal day, aimed at the Question 4 outcome.

- **Rhythm over word choice.** If it reads like someone else's cadence, fix that first.
- **Transitions are where drafts break.** No stitched-on connectors ("Furthermore," "That said," "It's worth noting") — use the author's actual connective tissue, often just the next sentence.
- **Audience calibration:** anything congregation-facing or public is written for unchurched readers — jargon explained or cut, warmth up front, one clear next step.

**Drafting constraints (apply before writing, not after):**
- Dashes only per Ark punctuation rules (for emphasis, no surrounding spaces) and sparingly — never as the default connector
- No runs of clipped dramatic fragments; vary sentence length naturally
- No cheesy setup phrases ("here's the thing," "what nobody tells you," "the truth is") — state the point
- No "not just X, but Y" constructions — say the point directly

## Phase 4: Polish — voice-protected pass

Apply Ark standards (reference file) and general quality to the draft, checking every word-level edit against the voice-protected list first:

- Generic polish would cut "just" as hedging → the author's style guide marks it as their softener → **keep it**
- Generic polish wants a tighter opener → the author always opens with a warm beat → **keep the beat**
- BUT: the author writes "Life Groups" or "12:00pm" → **Ark rules win, fix it** — personal style never overrides layer 1

## Phase 5: Deliver

Give the draft with minimal preamble, then a 2–4 line note: key structural choices, anywhere the personal guide and Ark rules pulled apart and how it resolved, anything worth revisiting.

## When it doesn't sound like them

Diagnose specifically — rhythm? word choice? a transition? a structural habit they don't have? Re-read that part of their style guide and rewrite the affected section, not the whole piece.
