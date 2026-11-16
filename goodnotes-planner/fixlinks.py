#!/usr/bin/env python3
"""Rewrite Chromium's named-destination links as explicit page links (/Fit).

GoodNotes, Notability and Apple PDFKit all follow explicit page destinations
reliably, so every internal tab/link keeps working after import.
"""
import sys
from pypdf import PdfReader, PdfWriter
from pypdf.generic import ArrayObject, NameObject, TextStringObject

src = sys.argv[1] if len(sys.argv) > 1 else "Atelier-Planner-2027.pdf"
reader = PdfReader(src)
writer = PdfWriter(clone_from=reader)

name_to_page = {}
for name, dest in reader.named_destinations.items():
    name_to_page[name.lstrip("/")] = reader.get_destination_page_number(dest)

fixed = missing = 0
for page in writer.pages:
    for a in page.get("/Annots") or []:
        a = a.get_object()
        if a.get("/Subtype") != "/Link":
            continue
        dest = a.get("/Dest")
        if dest is None:
            continue
        key = str(dest).lstrip("/")
        if key not in name_to_page:
            missing += 1
            continue
        target = writer.pages[name_to_page[key]].indirect_reference
        a[NameObject("/Dest")] = ArrayObject([target, NameObject("/Fit")])
        fixed += 1

writer.add_metadata({"/Title": "Atelier Planner 2027", "/Author": "Atelier",
                     "/Subject": "Digital planner for GoodNotes (landscape iPad, 4:3)"})
writer.write(src)
print(f"links rewritten: {fixed}, unresolved: {missing}")
