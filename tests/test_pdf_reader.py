from __future__ import annotations

import os
import tempfile

import fitz

from odt.document.pdf_reader import read_pdf_to_document


def _make_sample_pdf(path: str) -> None:
    doc = fitz.open()
    # single page with controlled size
    page = doc.new_page(width=300, height=200)
    # Insert two text spans with different fonts/sizes/colors
    page.insert_text((50, 50), "Hello PDF", fontsize=12, fontname="Times-Roman", color=(0, 0, 1))
    page.insert_text((50, 80), "Bold Text", fontsize=16, fontname="Times-Bold", color=(1, 0, 0))
    doc.save(path)


def test_read_pdf_basic(tmp_path):
    fpath = tmp_path / "sample.pdf"
    _make_sample_pdf(str(fpath))

    doc = read_pdf_to_document(str(fpath))

    # page count
    assert len(doc.pages) == 1

    page = doc.pages[0]
    # page size approximately matches created size
    assert abs(page.width - 300.0) < 1.0
    assert abs(page.height - 200.0) < 1.0

    # text extraction: we expect at least two text spans
    texts = [el.text for el in page.elements if hasattr(el, "text")]
    assert any("Hello" in t for t in texts)
    assert any("Bold" in t for t in texts)

    # bounding boxes present and sized
    bboxes = [el.bbox for el in page.elements if hasattr(el, "bbox")]
    assert all(getattr(bb, "width") > 0 for bb in bboxes)
    assert all(getattr(bb, "height") > 0 for bb in bboxes)

    # font info present
    styles = [el.style for el in page.elements if getattr(el, "style", None) is not None]
    assert any(s.font_size and s.font_size > 0 for s in styles)
    assert any(s.font_family for s in styles)
