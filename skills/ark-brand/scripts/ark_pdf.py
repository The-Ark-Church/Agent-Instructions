"""
ark_pdf.py — Build Ark Church-branded PDFs with one small, consistent API.

Styling (colors, logo, fonts, layout) is handled for you from the bundled brand
assets, per knowledge-base/ark-brand-kit.json:
  - Blue #1864ea dominant · Light Blue #74bdff secondary · Yellow #e0ff00 accent
    (sparingly) · Cream #f6f5e7 neutral · Black text
  - Smile Logo (primary wordmark) as letterhead; Boat Logo in the footer
  - Montserrat (the brand's sanctioned fallback for the licensed Gotham)

You supply the CONTENT; the brand look is automatic.

Requires: reportlab, pillow  (pip install reportlab pillow ; add
--break-system-packages if needed). Charts need matplotlib; the visual-QA
preview needs pypdfium2. No fonts are installed on the machine — the TTFs are
read from this skill's assets/ and subset-embedded, so this works in a
locked-down Cowork sandbox with no admin rights.

Usage:
    from ark_pdf import ArkDoc, today_brand_date, preview_images
    doc = ArkDoc("Weekly Ministry Update", subtitle="Ark Kids · The Ark Church", date=today_brand_date())
    doc.heading("This week")
    doc.paragraph("We saw <b>42</b> kids on Sunday.")
    doc.callout("Serve day is Saturday, August 9 — sign up at the kiosk.")
    doc.bullets(["New check-in kiosks are live", "Two families connected"])
    doc.table(["Service", "Kids"], [["9:00am", "24"], ["11:00am", "18"]])
    doc.image("attendance_chart.png", caption="Kids attendance, last 8 weeks")
    doc.save("out.pdf")

ALWAYS finish with a visual pass (see SKILL.md): render the pages with
preview_images("out.pdf") and LOOK at them — check the header size, that callout
/ code boxes are sized to their content, that tables and charts don't run off the
page — then fix and rebuild before delivering.
"""
from pathlib import Path

_BASE = Path(__file__).resolve().parents[1]          # skills/ark-brand/
_FONTS = _BASE / "assets" / "fonts"
_LOGOS = _BASE / "assets" / "logos"
_EMOJI = _BASE / "assets" / "emoji"

# --- Ark brand palette (ark-brand-kit.json) ---
BLUE = "#1864ea"       # primary — dominant
LIGHT_BLUE = "#74bdff"  # secondary
YELLOW = "#e0ff00"     # accent — sparingly
CREAM = "#f6f5e7"      # neutral
INK = "#14171C"        # body text (Black)
GREY = "#5B6570"
CALLOUT_BG = "#eef3fe"  # a light Blue tint for callout boxes (on-palette)

# Recommended categorical order for chart series (matplotlib), on-brand:
CHART_COLORS = [BLUE, LIGHT_BLUE, "#0d3f9e", YELLOW, GREY, INK]

# The Ark's approved emoji (org standards). Rendered as inline full-color images
# because Montserrat has no emoji glyphs. Keyed by the base char (variation
# selector U+FE0F is stripped before matching). Anything not on this list is left
# as-is (and will render blank) — the approved set is the allowed set.
APPROVED_EMOJI = {
    "😃": "1f603", "😁": "1f601", "😎": "1f60e", "🤣": "1f923", "😊": "1f60a",
    "🤗": "1f917", "🤔": "1f914", "🫡": "1fae1", "😳": "1f633", "🤯": "1f92f",
    "👍": "1f44d", "🙌": "1f64c", "👏": "1f44f", "👀": "1f440", "🙏": "1f64f",
    "❤": "2764", "❗": "2757", "🔥": "1f525", "🥳": "1f973", "🎉": "1f389",
}


def _emojify(text, px=12):
    """Replace approved emoji with inline image tags sized to the text."""
    if not text:
        return text
    t = str(text).replace("️", "")   # drop variation selector so base chars match
    for ch, code in APPROVED_EMOJI.items():
        if ch in t:
            tag = '<img src="%s" width="%d" height="%d" valign="-2"/>' % (_EMOJI / (code + ".png"), px, px)
            t = t.replace(ch, tag)
    return t


_FONTS_REGISTERED = False


def _ensure_deps():
    try:
        import reportlab  # noqa: F401
        import PIL  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "ark_pdf needs reportlab and pillow:\n"
            "    python3 -m pip install reportlab pillow\n"
            "(add --break-system-packages if the environment requires it)."
        ) from e


def _register_fonts():
    global _FONTS_REGISTERED
    if _FONTS_REGISTERED:
        return
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    from reportlab.pdfbase.pdfmetrics import registerFontFamily
    pdfmetrics.registerFont(TTFont("Mont", str(_FONTS / "Montserrat-Regular.ttf")))
    pdfmetrics.registerFont(TTFont("Mont-Med", str(_FONTS / "Montserrat-Medium.ttf")))
    pdfmetrics.registerFont(TTFont("Mont-SB", str(_FONTS / "Montserrat-SemiBold.ttf")))
    pdfmetrics.registerFont(TTFont("Mont-XB", str(_FONTS / "Montserrat-ExtraBold.ttf")))
    registerFontFamily("Mont", normal="Mont", bold="Mont-SB", italic="Mont", boldItalic="Mont-SB")
    _FONTS_REGISTERED = True


def today_brand_date():
    """Today, Ark-formatted: 'Tuesday, July 21, 2026'. Drop the year in copy where
    it isn't needed — the style guide prefers 'Tuesday, July 21'."""
    from datetime import date
    return date.today().strftime("%A, %B %-d, %Y")


def preview_images(pdf_path, dpi=110, out_prefix=None):
    """Rasterize each page to a PNG so the agent can DO A VISUAL PASS before
    delivering. Returns the list of PNG paths. Uses pypdfium2 (no system deps):
    python3 -m pip install pypdfium2."""
    import os
    import tempfile
    try:
        import pypdfium2 as pdfium
    except ImportError as e:
        raise RuntimeError("preview_images needs pypdfium2:\n    python3 -m pip install pypdfium2") from e
    if out_prefix is None:
        # Write previews to a temp dir, NOT next to the deliverable, so output folders stay clean.
        name = os.path.splitext(os.path.basename(str(pdf_path)))[0]
        out_prefix = os.path.join(tempfile.gettempdir(), "arkpdf_preview_" + name)
    base = out_prefix
    doc = pdfium.PdfDocument(str(pdf_path))
    scale = dpi / 72.0
    paths = []
    for i in range(len(doc)):
        img = doc[i].render(scale=scale).to_pil()
        p = "%s-%d.png" % (base, i + 1)
        img.save(p)
        paths.append(p)
    return paths


class ArkDoc:
    # header presets: (logo alignment, space above logo in inches, gap below logo in pts)
    _HEADER_STYLES = {
        "classic":  {"align": "LEFT",   "top_in": 0.7,  "gap_below": 8},
        "centered": {"align": "CENTER", "top_in": 0.35, "gap_below": 2},
        "banner":   {"align": "BANNER", "top_in": 0.45, "gap_below": 6},
    }

    def __init__(self, title, subtitle="The Ark Church", date=None,
                 footer_note="The Ark Church", logo_width_in=1.7,
                 header_style="classic", top_margin_in=None):
        _ensure_deps()
        _register_fonts()
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.units import inch
        self._letter = letter
        self._inch = inch
        self.title = title
        self.subtitle = subtitle
        self.date = date
        self.footer_note = footer_note
        self._logo_w = logo_width_in * inch          # letterhead logo size (smaller default)
        self.content_width = letter[0] - 1.8 * inch   # 0.9" margins
        if header_style not in self._HEADER_STYLES:
            raise ValueError("header_style must be one of %s" % list(self._HEADER_STYLES))
        self._hdr = self._HEADER_STYLES[header_style]
        # explicit top_margin_in wins; otherwise use the style's preset
        self._top_margin = (top_margin_in if top_margin_in is not None else self._hdr["top_in"]) * inch
        self._story = []
        self._styles()
        self._letterhead()

    # ---------- styles ----------
    def _styles(self):
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT, TA_CENTER
        from reportlab.lib.colors import HexColor
        base = getSampleStyleSheet()
        self.S = {
            "h1": ParagraphStyle("h1", fontName="Mont-XB", fontSize=19, leading=23,
                                 textColor=HexColor(BLUE), alignment=TA_LEFT, spaceBefore=6, spaceAfter=2),
            "subt": ParagraphStyle("subt", fontName="Mont-Med", fontSize=10.5, textColor=HexColor(INK), spaceAfter=1),
            "meta": ParagraphStyle("meta", fontName="Mont", fontSize=9, textColor=HexColor(GREY), spaceAfter=8),
            "h2": ParagraphStyle("h2", fontName="Mont-XB", fontSize=13, textColor=HexColor(BLUE), spaceBefore=15, spaceAfter=5),
            "body": ParagraphStyle("body", fontName="Mont", fontSize=10, leading=14.5, textColor=HexColor(INK), spaceAfter=6),
            "monocell": ParagraphStyle("monocell", parent=base["Code"], fontName="Courier", fontSize=8.5,
                                       textColor=HexColor(INK), leading=12),
            "callout": ParagraphStyle("callout", fontName="Mont", fontSize=10, leading=14, textColor=HexColor(INK)),
            "cell": ParagraphStyle("cell", fontName="Mont", fontSize=9.5, leading=12.5, textColor=HexColor(INK)),
            "cellh": ParagraphStyle("cellh", fontName="Mont-SB", fontSize=9.5, leading=12.5, textColor=HexColor(CREAM)),
            "caption": ParagraphStyle("caption", fontName="Mont", fontSize=8.5, leading=11,
                                      textColor=HexColor(GREY), alignment=TA_CENTER, spaceBefore=3, spaceAfter=8),
        }

    def _letterhead(self):
        from reportlab.platypus import Image, Spacer, Paragraph, Table, TableStyle
        from reportlab.lib.utils import ImageReader
        from reportlab.lib.units import inch
        smile = _LOGOS / "SmileLogo_Blue.png"
        align, gap_below = self._hdr["align"], self._hdr["gap_below"]

        def _logo(halign):
            try:
                iw, ih = ImageReader(str(smile)).getSize()
                return Image(str(smile), width=self._logo_w,
                             height=self._logo_w * ih / iw, hAlign=halign)
            except Exception:
                return Spacer(1, 0)

        def _title_block():
            items = [Paragraph(self.title, self.S["h1"])]
            if self.subtitle:
                items.append(Paragraph(self.subtitle, self.S["subt"]))
            if self.date:
                items.append(Paragraph("Prepared %s" % self.date, self.S["meta"]))
            return items

        if align == "BANNER":
            # logo and title side by side on one row — most compact vertically
            logo_col = self._logo_w + 0.15 * inch
            tbl = Table([[_logo("CENTER"), _title_block()]],
                        colWidths=[logo_col, self.content_width - logo_col])
            tbl.setStyle(TableStyle([
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]))
            self._story.append(tbl)
        else:
            self._story.append(_logo(align))   # LEFT or CENTER
            self._story.append(Spacer(1, gap_below))
            self._story.extend(_title_block())

        self._story.append(self._accent_rule())
        self._story.append(Spacer(1, 6))

    def _accent_rule(self):
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.colors import HexColor
        yw = 0.5 * self._inch
        t = Table([["", ""]], colWidths=[yw, self.content_width - yw], rowHeights=[3])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), HexColor(YELLOW)),
            ("BACKGROUND", (1, 0), (1, 0), HexColor(LIGHT_BLUE)),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        return t

    # ---------- a correctly-sized background box (table cell, not paragraph bg) ----------
    def _box(self, text, style_key, bg, accent=None):
        from reportlab.platypus import Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.colors import HexColor
        cell = Paragraph(text, self.S[style_key])
        t = Table([[cell]], colWidths=[self.content_width])
        cmds = [
            ("BACKGROUND", (0, 0), (-1, -1), HexColor(bg)),
            ("TOPPADDING", (0, 0), (-1, -1), 9), ("BOTTOMPADDING", (0, 0), (-1, -1), 9),
            ("LEFTPADDING", (0, 0), (-1, -1), 12), ("RIGHTPADDING", (0, 0), (-1, -1), 12),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ]
        if accent:
            cmds.append(("LINEBEFORE", (0, 0), (0, -1), 3, HexColor(accent)))
        t.setStyle(TableStyle(cmds))
        self._story.append(t)
        self._story.append(Spacer(1, 6))
        return self

    # ---------- content API (chainable) ----------
    def heading(self, text):
        from reportlab.platypus import Paragraph
        self._story.append(Paragraph(_emojify(text, px=15), self.S["h2"]))
        return self

    def paragraph(self, html):
        from reportlab.platypus import Paragraph
        self._story.append(Paragraph(_emojify(html), self.S["body"]))
        return self

    def bullets(self, items):
        from reportlab.platypus import Paragraph, ListFlowable, ListItem
        from reportlab.lib.colors import HexColor
        self._story.append(ListFlowable(
            [ListItem(Paragraph(_emojify(t), self.S["body"]), value="•", leftIndent=16) for t in items],
            bulletType="bullet", bulletColor=HexColor(BLUE), leftIndent=10, spaceAfter=6))
        return self

    def callout(self, text):
        """A highlighted note box (light-blue tint + blue left bar), correctly sized."""
        return self._box(_emojify(text), "callout", CALLOUT_BG, accent=BLUE)

    def mono(self, text):
        """A monospaced code/literal box on cream, correctly sized to its content."""
        return self._box(text, "monocell", CREAM)

    def spacer(self, pts=6):
        from reportlab.platypus import Spacer
        self._story.append(Spacer(1, pts))
        return self

    def table(self, header, rows, col_ratios=None):
        """Branded table. Header repeats across page breaks; long cell text wraps.
        For very wide data prefer fewer columns or an embedded chart via .image()."""
        from reportlab.platypus import Table, TableStyle, Paragraph
        from reportlab.lib.colors import HexColor, white
        n = len(header)
        if col_ratios and len(col_ratios) == n:
            tot = float(sum(col_ratios))
            widths = [self.content_width * r / tot for r in col_ratios]
        else:
            widths = [self.content_width / n] * n
        data = [[Paragraph(str(h), self.S["cellh"]) for h in header]] + \
               [[Paragraph(_emojify("" if c is None else str(c), px=11), self.S["cell"]) for c in r] for r in rows]
        t = Table(data, colWidths=widths, hAlign="LEFT", repeatRows=1)
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), HexColor(BLUE)),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [white, HexColor(CREAM)]),
            ("LINEBELOW", (0, 0), (-1, -1), 0.4, HexColor("#D8D5CC")),
            ("LINEAFTER", (0, 0), (-2, -1), 0.4, HexColor("#E3E7EF")),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("TOPPADDING", (0, 0), (-1, -1), 5), ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ]))
        self._story.append(t)
        return self

    def image(self, path, width_in=None, caption=None):
        """Embed an image (e.g. a matplotlib chart rendered in Ark colors), aspect
        preserved, centered, capped to the content width. Optional caption below."""
        from reportlab.platypus import Image, Paragraph, Spacer
        from reportlab.lib.utils import ImageReader
        iw, ih = ImageReader(str(path)).getSize()
        w = (width_in * self._inch) if width_in else self.content_width
        w = min(w, self.content_width)
        self._story.append(Image(str(path), width=w, height=w * ih / iw, hAlign="CENTER"))
        if caption:
            self._story.append(Paragraph(caption, self.S["caption"]))
        else:
            self._story.append(Spacer(1, 6))
        return self

    # ---------- footer + build ----------
    def _footer(self, canvas, doc):
        from reportlab.lib.colors import HexColor
        inch = self._inch
        canvas.saveState()
        canvas.setStrokeColor(HexColor(LIGHT_BLUE))
        canvas.setLineWidth(1)
        canvas.line(0.9 * inch, 0.72 * inch, self._letter[0] - 0.9 * inch, 0.72 * inch)
        try:
            canvas.drawImage(str(_LOGOS / "BoatLogo_Blue.png"), 0.9 * inch, 0.5 * inch,
                             width=0.26 * inch, height=0.26 * inch, mask="auto", preserveAspectRatio=True)
        except Exception:
            pass
        canvas.setFont("Mont", 8)
        canvas.setFillColor(HexColor(GREY))
        canvas.drawString(1.28 * inch, 0.58 * inch, "%s  ·  Internal" % self.footer_note)
        canvas.setFont("Mont-SB", 8)
        canvas.setFillColor(HexColor(BLUE))
        canvas.drawRightString(self._letter[0] - 0.9 * inch, 0.58 * inch, "Page %d" % doc.page)
        canvas.restoreState()

    def save(self, path):
        from reportlab.platypus import SimpleDocTemplate
        inch = self._inch
        doc = SimpleDocTemplate(str(path), pagesize=self._letter, topMargin=self._top_margin,
                                bottomMargin=0.95 * inch, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                                title=self.title, author="The Ark Church")
        doc.build(self._story, onFirstPage=self._footer, onLaterPages=self._footer)
        return str(path)
