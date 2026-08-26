from __future__ import annotations

import shutil
from pathlib import Path
from typing import Optional

import pytest

from odt.text.measure import measure_text
from odt.font.manager import FontManager


def find_font_for_lang(lang: str) -> Optional[str]:
    # common font dirs
    common_dirs = [
        "/usr/share/fonts/truetype",
        "/usr/share/fonts",
        "/usr/local/share/fonts",
        str(Path.home() / ".local" / "share" / "fonts"),
    ]
    fm = FontManager(font_dirs=[d for d in common_dirs if Path(d).exists()])
    try:
        return fm.font_for(lang)
    except Exception:
        return None


@pytest.mark.parametrize("lang,text", [
    ("en", "Hello world"),
    ("hi", "नमस्ते"),
    ("kn", "ನಮಸ್ಕಾರ"),
])
def test_measure_basic_scripts(lang: str, text: str):
    font = find_font_for_lang(lang)
    if font is None:
        pytest.skip(f"No font found for {lang} on this system")

    m = measure_text(text, font, font_size=24)
    assert m["width"] > 0
    assert m["height"] > 0
    assert len(m["line_metrics"]) == 1


def test_measure_long_and_multiline():
    font = find_font_for_lang("en")
    if font is None:
        pytest.skip("No Latin font found on this system")

    short = "Short"
    long = "This is a much longer line of text to measure and ensure width grows accordingly."
    ms = measure_text(short, font, font_size=16)
    ml = measure_text(long, font, font_size=16)
    assert ml["width"] > ms["width"]

    multi = "Line one\nLine two is a bit longer\n第三行"  # include an unrelated script for variety
    mm = measure_text(multi, font, font_size=16, line_spacing=4)
    assert mm["height"] >= sum(l["height"] for l in mm["line_metrics"])
    assert len(mm["line_metrics"]) == 3
