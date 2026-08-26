from __future__ import annotations

import os
from pathlib import Path

import pytest

try:
    import fitz
except Exception:  # pragma: no cover - skip if pymupdf absent
    fitz = None  # type: ignore

try:
    from PIL import Image
except Exception:  # pragma: no cover - skip if pillow absent
    Image = None  # type: ignore

from odt.document.models import BoundingBox, TextBlock
from odt.document.pdf_translator import render_translated_pdf
from odt.font.manager import FontManager
from odt.text.fitter import TextFitter


pytestmark = pytest.mark.skipif(fitz is None or Image is None, reason="pymupdf or pillow not installed")


def create_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    # Insert sample text at known bbox
    rect = fitz.Rect(50, 50, 400, 100)
    page.insert_textbox(rect, "Design Pressure: 10 MPa, Tag: PV-1024", fontsize=12)
    doc.save(str(path))
    doc.close()


def test_render_translated_pdf(tmp_path: Path):
    inp = tmp_path / "in.pdf"
    out = tmp_path / "out.pdf"
    png = tmp_path / "out.png"
    create_sample_pdf(inp)

    # Create translated block corresponding to original
    bbox = BoundingBox(50, 50, 400, 100)
    block = TextBlock(id="t1", bbox=bbox, text="[en->hi] डिज़ाइन दबाव: 10 MPa, टैग: PV-1024", language=None)

    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    fitter = TextFitter()

    # ensure we have at least one font available
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available on system; skipping PDF rendering test")

    render_translated_pdf(str(inp), str(out), {1: [block]}, fm, fitter)

    assert out.exists()

    # Export visual fixture
    doc = fitz.open(str(out))
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    pix.save(str(png))
    doc.close()

    assert png.exists()
