"""
ark_pdf.py — Build Ark Church-branded PDFs with one small, consistent API.

Styling (colors, logo, fonts, layout) is handled for you from the bundled brand
assets, per knowledge-base/ark-brand-kit.json:
  - Blue #1864ea dominant · Light Blue #74bdff secondary · Yellow #e0ff00 accent
    (used sparingly) · Cream #f6f5e7 neutral · Black text
  - Smile Logo (primary wordmark) as letterhead; Boat Logo in the footer
  - Montserrat (the brand's sanctioned fallback for the licensed Gotham)

You supply the CONTENT; the brand look is automatic. Do not recolor outside the
palette or restyle — that's the point of the skill.

Requires: reportlab, pillow  (pip install reportlab pillow ; add
--break-system-packages if the environment needs it). No fonts are installed on
the machine — the TTFs are read from this skill's assets/ and subset-embedded in
the PDF, so this works in a locked-down Cowork sandbox with no admin rights.

Usage:
    from ark_pdf import ArkDoc
    doc = ArkDoc("Weekly Ministry Update", subtitle="Ark Kids · The Ark Church")
    doc.heading("This week")
    doc.paragraph("We saw <b>42</b> kids on Sunday, and three families connected.")
    doc.bullets(["Serve day is Saturday, August 9", "New check-in kiosks are live"])
    doc.table(["Service", "Kids"], [["9:00am", "24"], ["11:00am", "18"]])
    doc.save("/path/to/output.pdf")

Date/ministry-name/time formatting for the copy itself follows the Ark
Communications Style Guide — see reference/brand-kit.md (and the ark-writing-coach
skill for wording).
"""
from pathlib import Path

# --- resolve bundled assets relative to this file (works wherever the skill lives) ---
_BASE = Path(__file__).resolve().parents[1]          # skills/ark-brand/
_FONTS = _BASE / "assets" / "fonts"
_LOGOS = _BASE / "assets" / "logos"

# --- Ark brand palette (ark-brand-kit.json) ---
BLUE = "#1864ea"      # primary — dominant
LIGHT_BLUE = "#74bdff"  # secondary
YELLOW = "#e0ff00"    # accent — use sparingly
CREAM = "#f6f5e7"     # neutral
INK = "#14171C"       # body text (Black)
GREY = "#5B6570"

_FONTS_REGISTERED = False


def _ensure_deps():
    try:
        import reportlab  # noqa: F401
        import PIL  # noqa: F401
    except ImportError as e:
        raise RuntimeError(
            "ark_pdf needs reportlab and pillow. Install them first:\n"
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
    """Today formatted the Ark way: 'Tuesday, July 21, 2026'. (Drop the year in
    copy where it isn't needed — the style guide prefers 'Tuesday, July 21'.)"""
    from datetime import date
    return date.today().strftime("%A, %B %-d, %Y")


class ArkDoc:
    def __init__(self, title, subtitle="The Ark Church", date=None, footer_note="The Ark Church"):
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
        self.content_width = letter[0] - 1.8 * inch  # 0.9" margins
        self._story = []
        self._styles()
        self._letterhead()

    # ---------- styles ----------
    def _styles(self):
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_LEFT
        from reportlab.lib.colors import HexColor
        base = getSampleStyleSheet()
        self.S = {
            "h1": ParagraphStyle("h1", fontName="Mont-XB", fontSize=20, leading=24,
                                 textColor=HexColor(BLUE), alignment=TA_LEFT, spaceBefore=6, spaceAfter=2),
            "subt": ParagraphStyle("subt", fontName="Mont-Med", fontSize=10.5,
                                   textColor=HexColor(INK), spaceAfter=1),
            "meta": ParagraphStyle("meta", fontName="Mont", fontSize=9,
                                   textColor=HexColor(GREY), spaceAfter=8),
            "h2": ParagraphStyle("h2", fontName="Mont-XB", fontSize=13,
                                 textColor=HexColor(BLUE), spaceBefore=15, spaceAfter=5),
            "body": ParagraphStyle("body", fontName="Mont", fontSize=10, leading=14.5,
                                   textColor=HexColor(INK), spaceAfter=6),
            "mono": ParagraphStyle("mono", parent=base["Code"], fontSize=8.5, textColor=HexColor(INK),
                                   backColor=HexColor(CREAM), borderPadding=7, leading=12, spaceAfter=6),
            "cell": ParagraphStyle("cell", fontName="Mont", fontSize=9.5, leading=12.5, textColor=HexColor(INK)),
            "cellh": ParagraphStyle("cellh", fontName="Mont-SB", fontSize=9.5, leading=12.5, textColor=HexColor(CREAM)),
        }

    # ---------- building blocks ----------
    def _letterhead(self):
        from reportlab.platypus import Image, Spacer, Paragraph
        smile = _LOGOS / "SmileLogo_Blue.png"
        try:
            from reportlab.lib.utils import ImageReader
            iw, ih = ImageReader(str(smile)).getSize()
            w = 2.35 * self._inch
            self._story.append(Image(str(smile), width=w, height=w * ih / iw))
        except Exception:
            pass
        self._story.append(Spacer(1, 8))
        self._story.append(Paragraph(self.title, self.S["h1"]))
        if self.subtitle:
            self._story.append(Paragraph(self.subtitle, self.S["subt"]))
        if self.date:
            self._story.append(Paragraph("Prepared %s" % self.date, self.S["meta"]))
        self._story.append(self._accent_rule())
        self._story.append(Spacer(1, 6))

    def _accent_rule(self):
        from reportlab.platypus import Table, TableStyle
        from reportlab.lib.colors import HexColor
        yellow_w = 0.55 * self._inch
        t = Table([["", ""]], colWidths=[yellow_w, self.content_width - yellow_w], rowHeights=[3.5])
        t.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (0, 0), HexColor(YELLOW)),
            ("BACKGROUND", (1, 0), (1, 0), HexColor(LIGHT_BLUE)),
            ("TOPPADDING", (0, 0), (-1, -1), 0), ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0),
        ]))
        return t

    def heading(self, text):
        from reportlab.platypus import Paragraph
        self._story.append(Paragraph(text, self.S["h2"]))
        return self

    def paragraph(self, html):
        """A paragraph. Inline markup: <b>bold</b>, <font name='Courier'>code</font>."""
        from reportlab.platypus import Paragraph
        self._story.append(Paragraph(html, self.S["body"]))
        return self

    def bullets(self, items):
        from reportlab.platypus import Paragraph, ListFlowable, ListItem
        from reportlab.lib.colors import HexColor
        self._story.append(ListFlowable(
            [ListItem(Paragraph(t, self.S["body"]), value="•", leftIndent=16) for t in items],
            bulletType="bullet", bulletColor=HexColor(BLUE), leftIndent=10, spaceAfter=6))
        return self

    def mono(self, text):
        from reportlab.platypus import Paragraph
        self._story.append(Paragraph(text, self.S["mono"]))
        return self

    def spacer(self, pts=6):
        from reportlab.platypus import Spacer
        self._story.append(Spacer(1, pts))
        return self

    def table(self, header, rows, col_ratios=None):
        """A branded table. header: list of column titles. rows: list of row lists.
        col_ratios: optional relative widths, e.g. [1, 3]; defaults to equal."""
        from reportlab.platypus import Table, TableStyle, Paragraph
        from reportlab.lib.colors import HexColor, white
        n = len(header)
        if col_ratios and len(col_ratios) == n:
            tot = float(sum(col_ratios))
            widths = [self.content_width * r / tot for r in col_ratios]
        else:
            widths = [self.content_width / n] * n
        data = [[Paragraph(str(h), self.S["cellh"]) for h in header]] + \
               [[Paragraph("" if c is None else str(c), self.S["cell"]) for c in r] for r in rows]
        t = Table(data, colWidths=widths, hAlign="LEFT")
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
        doc = SimpleDocTemplate(str(path), pagesize=self._letter, topMargin=0.7 * inch,
                                bottomMargin=0.95 * inch, leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                                title=self.title, author="The Ark Church")
        doc.build(self._story, onFirstPage=self._footer, onLaterPages=self._footer)
        return str(path)
