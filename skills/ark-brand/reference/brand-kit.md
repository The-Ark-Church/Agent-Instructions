# The Ark Church — Brand Kit (condensed)

Full machine-readable source: [ark-brand-kit.json](ark-brand-kit.json). This is the working summary for building branded documents. The `ark_pdf.py` builder already applies the colors, logo, and font correctly — this file is for judgment calls and for non-PDF output.

## Colors

| Role | Name | Hex | Share | Use for |
|---|---|---|---|---|
| Primary | Blue | `#1864ea` | ~35% | Headlines, buttons, dominant surfaces, table headers |
| Secondary | Light Blue | `#74bdff` | ~35% | Accents, rules, secondary surfaces, gradients with Blue |
| Accent | Yellow | `#e0ff00` | ~20% | Calls to action, highlights — **use sparingly** |
| Neutral | Tan / Cream | `#f6f5e7` | ~5% | Backgrounds, cream surfaces, light text on dark |
| — | Black | `#000000` | ~5% | Body text, contrast, dark surfaces |

Keep **Blue and Light Blue dominant**. Yellow is a spark, not a field. Never introduce colors outside this palette.

## Logos

- **Smile Logo** — primary wordmark: "THE ARK CHURCH" arched ("the smile") with the circle boat icon. This is the default letterhead. `assets/logos/SmileLogo_{Blue,White,Cream,Black}.png`.
- **Boat Logo** — the boat icon alone. Good for footers, small marks. `assets/logos/BoatLogo_{Blue,White,Cream,Black}.png`.
- **Circle Logo** — boat knocked out of a solid circle.

Pick the variant that contrasts with its background (Blue or Black on light; White or Cream on dark). **Never stretch, recolor outside the palette, or otherwise alter the logos.**

## Typography

- **Gotham Ultra** (display/headlines) and **Gotham Medium** (body) are the brand fonts — licensed (Hoefler&Co), **not distributed**, and not usable in Cowork.
- **Montserrat** is the sanctioned fallback for web/system/automated contexts (this skill bundles it, OFL-licensed). Use ExtraBold for display, SemiBold for subheads, Regular/Medium for body.
- All-caps is a **display treatment only** — body copy is never all-caps.

## Written standards (apply to the copy)

- **Times:** 6:00pm · 8:00-9:30am · noon (never 12:00pm) · midnight (never 12:00am)
- **Dates:** Tuesday, April 28 — day of week, no ordinal ("28th"), no year unless needed
- **Phone:** 936-756-1988 (dashes) · **Oxford commas** always · one space between sentences · active voice
- **Names:** The Ark Church (formal) · The Ark (casual) · Ark Church (adjective) · never lowercase "the ark church"
- **Ministries (exact):** Ark Groups, Ark Care, Ark Kids, Ark Teams, Worship Ministry, Production Department, Biblical Life Coaching. Never: Life Groups, Life Care, Music Ministry, Praise Team, Tech Department, Biblical Counseling.
- **Religious style:** capitalize He/Him/His/You/Your for God, and Bible, Scripture, God's Word; lowercase biblical, scriptural, godly; don't abbreviate Bible books.
- **Tone:** authentic, informal, sincere, positive; written for unchurched people; explain or cut jargon; lead with what we want *for* people, not *from* them.

For substantive wording, use the **ark-writing-coach** skill, then lay the result out with this skill.
