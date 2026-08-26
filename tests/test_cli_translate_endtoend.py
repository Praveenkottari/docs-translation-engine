from __future__ import annotations

import os
from pathlib import Path

import pytest

from odt.cli import main

try:
    import fitz
except Exception:
    fitz = None

from odt.font.manager import FontManager


pytestmark = pytest.mark.skipif(fitz is None, reason="pymupdf not installed")


def create_sample_pdf(path: Path) -> None:
    doc = fitz.open()
    p = doc.new_page(width=595, height=842)
    r = fitz.Rect(50, 50, 400, 100)
    p.insert_textbox(r, "Design Pressure: 10 MPa, Tag: PV-1024", fontsize=12)
    doc.save(str(path))
    doc.close()


def test_cli_translate_endtoend(tmp_path: Path):
    inp = tmp_path / "in.pdf"
    out = tmp_path / "out.pdf"
    create_sample_pdf(inp)

    # ensure fonts available
    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available")

    rc = main(["translate", str(inp), "--target", "kn", "--output", str(out)])
    assert rc == 0
    assert out.exists()
