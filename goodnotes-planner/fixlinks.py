#!/usr/bin/env python3
"""Post-process the Chromium PDF for GoodNotes.

1. Rewrite named-destination links as explicit page links (/Fit), which
   GoodNotes, Notability and Apple PDFKit all follow reliably.
2. Add a nested PDF outline (bookmarks): month > week > day, shown in
   GoodNotes' Outline panel.
"""
import datetime as dt
import json
import sys
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject

sys.path.insert(0, str(Path(__file__).parent))
import almanac  # noqa: E402

HERE = Path(__file__).parent
src = sys.argv[1] if len(sys.argv) > 1 else str(HERE / "Atelier-Planner-2027.pdf")
reader = PdfReader(src)
writer = PdfWriter(clone_from=reader)

name_to_page = {name.lstrip("/"): reader.get_destination_page_number(dest)
                for name, dest in reader.named_destinations.items()}

fixed = missing = 0
for page in writer.pages:
    for a in page.get("/Annots") or []:
        a = a.get_object()
        if a.get("/Subtype") != "/Link" or a.get("/Dest") is None:
            continue
        key = str(a["/Dest"]).lstrip("/")
        if key not in name_to_page:
            missing += 1
            continue
        a[NameObject("/Dest")] = ArrayObject([writer.pages[name_to_page[key]].indirect_reference, NameObject("/Fit")])
        fixed += 1

# ---------------------------------------------------------------- outline
info = json.loads((HERE / "outline.json").read_text())
order = info["order"]
YEAR = 2027
HOL = almanac.kr_holidays(YEAR)
MONTHS = ["January", "February", "March", "April", "May", "June", "July",
          "August", "September", "October", "November", "December"]
SINGLE = {"cover": "Cover", "index": "Index", "year": "Year at a Glance", "goals": "Intentions",
          "color": "Sun Rings - Year in Color", "birthdays": "Birthdays & Days to Keep",
          "yreview": f"{YEAR} - The Year, Kept", "notes": "Notes", "dots": "Dots & Drafts"}
SECTION = {"o": "Opener", "m": "Calendar", "h": "Rituals - Habit Tracker", "r": "Month in Review"}

month_node = week_node = None
cur_month = None
for i, pid in enumerate(order):
    if pid in SINGLE:
        writer.add_outline_item(SINGLE[pid], i)
        month_node = week_node = None
        continue
    kind = pid[0]
    if kind in "omhr" and pid[1:].isdigit():
        m = int(pid[1:])
        if kind == "o":
            month_node = writer.add_outline_item(f"{m:02d}  {MONTHS[m - 1]}", i)
            cur_month, week_node = m, None
        writer.add_outline_item(SECTION[kind], i, parent=month_node)
        if kind == "r":
            week_node = None
    elif kind == "w":
        y, w = map(int, pid[1:].split("-"))
        start = dt.date.fromisocalendar(y, w, 1)
        end = start + dt.timedelta(days=6)
        title = f"Week {w:02d}  {start:%b} {start.day} - {end:%b} {end.day}"
        week_node = writer.add_outline_item(title, i, parent=month_node)
    elif kind == "d":
        d = dt.date.fromisoformat(pid[1:])
        if d.month != cur_month:
            week_node = None
        title = f"{d:%a} {d:%b} {d.day}" + (f"  - {HOL[d]}" if d in HOL else "")
        writer.add_outline_item(title, i, parent=week_node or month_node)

writer.page_mode = "/UseOutlines"
writer.add_metadata({"/Title": f"Atelier Soleil {YEAR}", "/Author": "Atelier Soleil",
                     "/Subject": "Hyperlinked digital planner for GoodNotes (landscape iPad, 4:3)"})
writer.compress_identical_objects(remove_duplicates=True, remove_unreferenced=True)
writer.write(src)
print(f"links rewritten: {fixed}, unresolved: {missing}, pages: {len(writer.pages)}")
