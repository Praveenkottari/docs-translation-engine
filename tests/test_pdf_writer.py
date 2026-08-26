from __future__ import annotations

import os

import fitz

from odt.document.pdf_reader import read_pdf_to_document
from odt.document.pdf_writer import write_document_to_pdf


def _make_sample_pdf(path: str) -> None:
    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    page.insert_text((60, 60), "Roundtrip Test", fontsize=14, fontname="Helvetica", color=(0, 0, 0))
    page.insert_text((60, 90), "Second line", fontsize=12, fontname="Helvetica", color=(0, 0, 1))
    doc.save(path)


def test_pdf_roundtrip(tmp_path):
    in_pdf = tmp_path / "in.pdf"
    out_pdf = tmp_path / "out.pdf"

    _make_sample_pdf(str(in_pdf))

    doc = read_pdf_to_document(str(in_pdf))
    # write back
    write_document_to_pdf(doc, str(out_pdf))

    # read output
    out_doc = read_pdf_to_document(str(out_pdf))

    # compare page count
    assert len(doc.pages) == len(out_doc.pages)

    # compare dimensions
    for a, b in zip(doc.pages, out_doc.pages):
        assert abs(a.width - b.width) < 1.0
        assert abs(a.height - b.height) < 1.0

    # compare concatenated text
    def page_text(d):
        parts = [el.text for el in d.pages[0].elements if hasattr(el, "text")]
        return "\n".join(parts)

    assert "Roundtrip Test" in page_text(doc)
    assert "Roundtrip Test" in page_text(out_doc)

    # write a visual fixture for later manual checks
    fixtures_dir = os.path.join(os.getcwd(), "tests", "fixtures")
    os.makedirs(fixtures_dir, exist_ok=True)
    fixture_path = os.path.join(fixtures_dir, "roundtrip_out.pdf")
    # copy the output as a visual fixture
    with open(out_pdf, "rb") as src, open(fixture_path, "wb") as dst:
        dst.write(src.read())
