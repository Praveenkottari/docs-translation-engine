from __future__ import annotations

import os
from pathlib import Path

import pytest

from odt.cli import main

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = None

try:
    import fitz
except Exception:
    fitz = None

from odt.font.manager import FontManager


pytestmark = pytest.mark.skipif(Image is None or fitz is None, reason="Pillow or PyMuPDF not installed")


def create_sample_image(path: Path) -> None:
    img = Image.new("RGB", (600, 200), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)
    try:
        f = ImageFont.load_default()
    except Exception:
        f = None
    draw.text((10, 50), "Pressure: 5.5 MPa; Tag: PV-2048", fill=(0, 0, 0), font=f)
    img.save(str(path), format="PNG")


def test_cli_translate_image_endtoend(tmp_path: Path):
    inp = tmp_path / "in.png"
    out = tmp_path / "out.pdf"
    create_sample_image(inp)

    # ensure fonts available
    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        _ = fm.font_for("en")
    except Exception:
        pytest.skip("No usable fonts available")

    rc = main(["translate", str(inp), "--target", "kn", "--output", str(out)])
    assert rc == 0
    assert out.exists()
