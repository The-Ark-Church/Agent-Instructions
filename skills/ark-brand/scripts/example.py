#!/usr/bin/env python3
"""
Complete, runnable example of building an Ark-branded PDF with ark_pdf.
Run it from anywhere:  python3 example.py  ->  writes ark-brand-example.pdf in the cwd.
Copy this pattern into your own driver script; swap in real content.
"""
import os
import sys

# Import the builder from this same scripts/ folder, wherever the skill lives.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ark_pdf import ArkDoc, today_brand_date

doc = ArkDoc(
    "Volunteer Serve Day — August 9",
    subtitle="Ark Teams · The Ark Church",
    date=today_brand_date(),
)

doc.heading("What's happening")
doc.paragraph(
    "We're setting up the campus for the fall launch, and we'd love your help. "
    "Come for the morning, stay for lunch, and leave knowing you helped hundreds "
    "of people walk into something ready for them."
)

doc.heading("The details")
doc.bullets([
    "Saturday, August 9, 8:00-11:30am",
    "Main Campus — meet in the lobby",
    "Lunch, coffee, and childcare provided",
    "Text 936-756-1988 with any questions",
])

doc.heading("Where we need hands")
doc.table(
    ["Team", "Roles open", "Lead"],
    [["Production Department", "4", "Ready"],
     ["Ark Kids", "6", "Ready"],
     ["Worship Ministry", "2", "Ready"]],
    col_ratios=[2, 1, 1],
)

doc.paragraph("Thank you for serving. It matters more than you know.")

out = os.path.join(os.getcwd(), "ark-brand-example.pdf")
print("Wrote", doc.save(out))
