from __future__ import annotations

from pathlib import Path

import pytest

try:
    import fitz
    from PIL import Image, ImageDraw
except Exception:
    fitz = None

from odt.document.scanned_translator import render_translated_scanned_pdf
from odt.document.models import BoundingBox, TextBlock
from odt.font.manager import FontManager
from odt.text.fitter import TextFitter


pytestmark = pytest.mark.skipif(fitz is None, reason="pymupdf or pillow not installed")


def create_scanned_pdf_with_text(path: Path, text: str, bbox=(50, 50, 400, 100)) -> None:
    # create image with text and a graphic element
    img = Image.new("RGB", (595, 842), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    # draw a rectangle graphic
    draw.rectangle([100, 200, 200, 300], outline=(255, 0, 0), width=3)
    draw.text((bbox[0], bbox[1]), text, fill=(0, 0, 0))
    tmp = path.with_suffix(".png")
    img.save(tmp)

    doc = fitz.open()
    page = doc.new_page(width=595, height=842)
    page.insert_image(page.rect, filename=str(tmp))
    doc.save(str(path))
    doc.close()
    tmp.unlink()


def test_scanned_simple_page(tmp_path: Path):
    inp = tmp_path / "scan.pdf"
    out = tmp_path / "scan_out.pdf"
    png = tmp_path / "scan_out.png"
    text = "Design Pressure: 10 MPa"
    create_scanned_pdf_with_text(inp, text)

    bbox = BoundingBox(50, 50, 400, 100)
    block = TextBlock(id="s1", bbox=bbox, text="[en->hi] डिज़ाइन दबाव: 10 MPa", language=None)

    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available on system; skipping scanned PDF rendering test")

    fitter = TextFitter()
    render_translated_scanned_pdf(str(inp), str(out), {1: [block]}, fm, fitter)
    assert out.exists()

    # Export visual fixture
    doc = fitz.open(str(out))
    pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
    pix.save(str(png))
    doc.close()
    assert png.exists()


def test_scanned_multiple_blocks(tmp_path: Path):
    inp = tmp_path / "scan2.pdf"
    out = tmp_path / "scan2_out.pdf"
    text = "Value A: 100\nValue B: 200"
    create_scanned_pdf_with_text(inp, text)

    b1 = TextBlock(id="s1", bbox=BoundingBox(50, 50, 300, 80), text="[en->ta] मूल्य A: 100", language=None)
    b2 = TextBlock(id="s2", bbox=BoundingBox(50, 80, 300, 120), text="[en->ta] मूल्य B: 200", language=None)

    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available on system; skipping scanned PDF rendering test")

    fitter = TextFitter()
    render_translated_scanned_pdf(str(inp), str(out), {1: [b1, b2]}, fm, fitter)
    assert out.exists()


def test_scanned_mixed_text_image(tmp_path: Path):
    inp = tmp_path / "scan3.pdf"
    out = tmp_path / "scan3_out.pdf"
    text = "Header"
    create_scanned_pdf_with_text(inp, text)

    b = TextBlock(id="s1", bbox=BoundingBox(50, 50, 300, 80), text="[en->kn] ಹೆಡರ್", language=None)

    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available on system; skipping scanned PDF rendering test")

    fitter = TextFitter()
    render_translated_scanned_pdf(str(inp), str(out), {1: [b]}, fm, fitter)
    assert out.exists()
