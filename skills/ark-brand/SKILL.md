---
name: ark-brand
description: Produce Ark Church-branded PDFs and documents with the official brand kit applied automatically — Ark Blue/Light Blue/Yellow/Cream colors, the Smile Logo, and Montserrat — so staff get on-brand output without knowing the rules. Use whenever someone asks to create or generate a PDF, report, one-pager, handout, flyer, overview, summary, or document for The Ark, or says "make this a PDF," "brand this," "style this document," "add our branding," or "use our colors/logo." Default to Ark branding when the user hasn't specified a style; if they give their own styling, follow that instead. Handles the visual layer; ark-writing-coach handles the wording.
---

# Ark Brand — Branded Documents

You turn content into on-brand Ark Church documents. The staff member supplies what to say; you apply the visual brand automatically, from this skill's bundled assets. They should never need to know the palette, own a font, or install anything.

**Default to branding.** If someone asks for a PDF/report/handout for The Ark and doesn't specify a look, make it Ark-branded — don't hand back a generic document. Only skip branding if they ask for something plainly un-branded (a raw data export, a fill-in form) or provide their own styling.

## How to build (PDF)

Use the bundled builder `scripts/ark_pdf.py` — it handles colors, the Smile Logo letterhead, Montserrat, tables, and the footer. You supply content through a small API.

1. **Ensure dependencies** (no font install — the TTFs are read from this skill and embedded in the PDF, so this works in a locked-down Cowork sandbox):
   ```
   python3 -m pip install reportlab pillow      # always
   python3 -m pip install matplotlib            # only if the document has charts
   python3 -m pip install pypdfium2             # for the required visual pass (step 3)
   ```
2. **Write a short driver script** and run it. Minimal example:
   ```python
   import sys; sys.path.insert(0, "<path to this skill>/scripts")
   from ark_pdf import ArkDoc, today_brand_date

   doc = ArkDoc("Weekly Ministry Update", subtitle="Ark Kids · The Ark Church", date=today_brand_date())
   doc.heading("This week")
   doc.callout("Serve day is Saturday, August 9 — sign up at the kiosk.")
   doc.paragraph("We saw <b>42</b> kids on Sunday, and three families connected.")
   doc.bullets(["New check-in kiosks are live", "Two families connected"])
   doc.table(["Service", "Kids"], [["9:00am", "24"], ["11:00am", "18"]], col_ratios=[1, 1])
   doc.save("/path/to/output.pdf")
   ```
   `scripts/example.py` is a complete, runnable version to copy from.
3. **Do the visual pass (REQUIRED — don't skip).** Rasterize the pages and actually look at them before you hand anything over:
   ```python
   from ark_pdf import preview_images
   for p in preview_images("/path/to/output.pdf"):
       ...  # open/view each PNG
   ```
   View every page image and check: the header/logo isn't oversized; callout and code boxes hug their content (not the whole column, not overflowing); tables and charts fit inside the margins and don't clip; page breaks are clean; nothing overlaps. **If anything's off, fix the driver and rebuild** — then look again. Only deliver a PDF you've seen.
4. **Share the PDF** with the user.

### The content API (all methods chainable)
- `ArkDoc(title, subtitle=..., date=..., logo_width_in=1.7)` — sets up the letterhead (Smile Logo + title + accent rule). `date=today_brand_date()` for the Ark date format. `logo_width_in` shrinks/grows the header logo (default 1.7").
- `.heading(text)` — a blue section heading.
- `.paragraph(html)` — body text. Inline markup: `<b>bold</b>`, `<font name='Courier'>literal/code</font>`.
- `.bullets([...])` — a bulleted list.
- `.callout(text)` — a highlighted note box (light-blue tint + blue left bar), sized to its content.
- `.table(header, rows, col_ratios=None)` — branded table; `col_ratios` sets relative widths (e.g. `[1, 3]`). Header repeats across page breaks; long cell text wraps.
- `.mono(text)` — a monospaced code/literal box on cream, sized to its content.
- `.image(path, width_in=None, caption=None)` — embed an image (e.g. a chart), aspect preserved, centered.
- `.save(path)` — writes the PDF.

### Charts & complex tables
- **Charts:** the builder doesn't draw charts — render them with **matplotlib in Ark colors**, save a PNG, and embed with `.image(path, caption=...)`. Import the palette: `from ark_pdf import CHART_COLORS, BLUE, LIGHT_BLUE, YELLOW`. Use `CHART_COLORS` for categorical series (Blue → Light Blue → dark Blue → Yellow → grey → black), keep Blue dominant, and use Yellow only to spotlight one value. For full brand consistency, point matplotlib at the bundled Montserrat (`font_manager.fontManager.addfont(...assets/fonts/Montserrat-Regular.ttf)`, then `rcParams["font.family"]="Montserrat"`). Keep figures ≤ ~7" wide so they fit the margins. (You can lean on the `dataviz` skill for chart design — just apply the Ark palette.)
- **Wide/long tables:** `.table()` repeats the header across page breaks and wraps long cell text. For genuinely wide data, prefer fewer columns, split into two tables, or summarize as a chart — a table that overflows the page reads worse than a chart. Step 3's visual pass is where you catch overflow.

## Apply the written standards to the copy

The look is handled; the *words* still follow the Ark Communications Style Guide — see [reference/brand-kit.md](reference/brand-kit.md). The ones that bite:
- **Times:** 6:00pm · 8:00-9:30am · noon (never 12:00pm) · midnight (never 12:00am)
- **Dates:** Tuesday, April 28 — day of week, no "28th," no year unless needed
- **Phone:** 936-756-1988 · **Oxford commas** always · no all-caps in copy
- **Ministry names:** Ark Groups, Ark Care, Ark Kids, Ark Teams, Worship Ministry, Production Department, Biblical Life Coaching — never Life Groups, Music Ministry, Tech Department, etc.
- **The Ark Church** (formal) / **The Ark** (casual) / **Ark Church** (adjective) — never lowercase.
- **Emoji work** — The Ark's ~20 approved emoji render automatically as inline full-color images; just type them (😃 🎉 🙌 🙏 ❤️ 🔥 👍 …). Montserrat has no emoji glyphs, so the builder swaps approved emoji for bundled images (`assets/emoji/`, Twemoji CC-BY). Emoji outside the approved list have no asset and won't render — which keeps output to the approved set.

For anything beyond light formatting, run the copy through the **ark-writing-coach** skill first, then lay it out here.

## The brand (quick reference — full kit in reference/)
- **Colors:** Blue `#1864ea` (primary, dominant) · Light Blue `#74bdff` (secondary) · Yellow `#e0ff00` (accent, sparingly) · Cream `#f6f5e7` (neutral) · Black. The builder uses these correctly by default.
- **Logo:** the Smile Logo (primary wordmark) is placed for you. Never stretch, recolor, or alter any logo.
- **Font:** Montserrat — the brand's sanctioned fallback for the licensed Gotham (which isn't distributable). Bundled in `assets/fonts/` (OFL).
- Full machine-readable kit: [reference/ark-brand-kit.json](reference/ark-brand-kit.json).

## Notes
- **Self-contained:** everything (logos, fonts, brand kit) is inside this skill folder — no network, no external references, no admin rights needed.
- **Non-PDF requests:** for on-brand HTML, slides, or email, reuse the same palette, Smile Logo, and Montserrat/`Montserrat` fallback and the usage rules in reference/. (The bundled builder is PDF-focused today.)
- **Gotham:** intentionally not bundled — it's a licensed font that can't be redistributed. Montserrat is the correct, brand-approved substitute for staff/Cowork use.
