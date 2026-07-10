---
name: build-my-style-guide
description: Create a personal writing style guide through a short guided interview — no writing samples required. Use when an Ark staff member wants Claude to write in their voice, says "build my style guide," "set up my writing style," "make it sound like me," or is onboarding to Claude and wants personalized writing help. Run once; the result powers write-like-me ghostwriting.
---

# Build My Style Guide

<!-- Adapted for The Ark Church from Triumph Tech's rock-claude-plugins (Apache 2.0). -->

This skill captures how a specific Ark staff member actually writes, through a short writing interview. Instead of asking them to describe their style in the abstract, it asks them to write small pieces — the kinds of things Ark staff send every week. Those samples reveal voice, rhythm, and mechanics better than any questionnaire.

**The personal guide complements the Ark Communications Style Guide — it never overrides it.** Ark rules (times, dates, ministry names, tone for unchurched people) always win; the personal guide covers everything the Ark guide leaves open: greeting style, warmth, sentence rhythm, sign-offs, directness.

## What this produces

A personal style guide document containing:
- Specific, actionable voice rules derived from their actual writing
- Quick templates for their common situations (announcement, congregation email, internal message, social post, pastoral note)
- An explicit avoid list

**Where it's saved:** in Claude Code, write it to `context/style-guide.md` in their workspace. On claude.ai, produce it as a document and tell them to add it to their Claude project (or paste it at the start of writing sessions) so `write-like-me` can find it.

## How to run the interview

Ask each question **individually, one at a time**. Wait for the response before the next question. Keep transitions to one line — this should feel like a quick writing exercise, not a form.

Open with:

> "This is a short writing interview that captures your voice, so Claude can draft things that actually sound like you. I'll ask 8 quick writing prompts — just write naturally, the way you actually would. Takes about 10 minutes.
>
> One important note: don't paste in AI-generated or heavily polished text. Write fresh, or paste something you wrote yourself that never went through an AI tool. If it doesn't sound like your unedited self, the style guide won't either."

Then ask their first name (it titles the guide).

## The Questions

### Q1 — Sunday announcement
> "Write a short announcement for an upcoming event — the kind that goes in the bulletin or gets read from the stage. Pick any real or made-up event. 3 to 5 sentences."

*Reveals:* how they open, energy level, whether they lead with the event or the person, call-to-action style.

### Q2 — Email to the congregation
> "Open an email to the whole congregation about that same event. Write the greeting and first 3 to 4 sentences."

*Reveals:* greeting format, warmth before business, how their register changes for a broad external audience.

### Q3 — Internal staff message
> "Now tell the staff team about the same event in your team chat or email — what you'd actually type. 2 to 4 sentences."

*Reveals:* the internal-voice shift, abbreviations, directness, whether formality drops.

### Q4 — Delivering a change
> "A volunteer event has to move by one week. Write the full message to the volunteers — 3 to 6 sentences."

*Reveals:* lead with the fact or cushion first, how they attribute cause, what follows the hard line.

### Q5 — Urgent ask
> "You need something from a teammate by end of day. Write the full message — greeting, one line of context, the ask, and anything you'd add at the end. 3 to 5 sentences."

*Reveals:* directness under pressure, hedging and softeners ("just," "quick"), closers.

### Q6 — Social media post
> "Write an Instagram caption for an event or a Sunday moment — exactly what you'd post, hashtags and all if you'd use them."

*Reveals:* public voice, emoji instincts, hashtag habits, brevity.

### Q7 — Pastoral note
> "Someone emailed asking for prayer about a hard situation. Write your reply — 2 to 4 sentences."

*Reveals:* pastoral register, how faith language shows up naturally, sincerity patterns, whether they promise action.

### Q8 — Celebration
> "A volunteer just hit a milestone, or a new family joined — welcome or celebrate them in a short message. 2 to 4 sentences."

*Reveals:* exclamation habits, warmth vocabulary, how celebration differs from their baseline.

## Building the guide

After Q8, analyze all eight samples together and produce the style guide with these sections:

1. **Voice summary** — 2-3 sentences describing their natural voice
2. **Voice rules** — specific and mechanical, drawn from evidence ("Greets with 'Hey [name]!' internally, 'Hi friends' broadly"; "Short sentences, average 8-12 words"; "One exclamation point max, lands on the celebration, never the ask")
3. **Register shifts** — how congregation / internal / pastoral / social voices differ
4. **Templates** — a skeleton for each: announcement, congregation email, internal message, social post, pastoral note
5. **Avoid list** — words, constructions, and habits that would sound wrong coming from them
6. A closing line: *"This guide works together with the Ark Communications Style Guide — Ark rules always apply on top."*

Title it "[Name]'s Writing Style Guide" with the date. Show them the result, ask if anything feels off, and adjust before saving.
