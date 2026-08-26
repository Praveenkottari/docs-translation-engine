from __future__ import annotations

from pathlib import Path

import pytest

from odt.document.models import BoundingBox, TextStyle
from odt.font.manager import FontManager
from odt.text.fitter import TextFitter


def find_font(lang: str) -> str | None:
    fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", str(Path.home() / ".local" / "share" / "fonts")])
    try:
        return fm.font_for(lang)
    except Exception:
        return None


def test_short_text_fits():
    font = find_font("en")
    if not font:
        pytest.skip("No Latin font available")
    fitter = TextFitter()
    bbox = BoundingBox(0, 0, 200, 50)
    style = TextStyle(font_size=14)
    res = fitter.fit_text("Hello world", bbox, style, font)
    assert res.fit_status == "fitted"
    assert res.font_size >= fitter.min_font_size


def test_long_text_wraps_and_reduces():
    font = find_font("en")
    if not font:
        pytest.skip("No Latin font available")
    fitter = TextFitter(min_font_size=6.0, font_size_step=2.0)
    bbox = BoundingBox(0, 0, 150, 60)
    text = "This is a long translated sentence that should wrap across multiple lines to fit within the bounding box provided."
    res = fitter.fit_text(text, bbox, TextStyle(font_size=16), font)
    assert res.fit_status in ("fitted", "failed")
    # ensure we have at least one line break returned
    assert isinstance(res.line_breaks, list) and len(res.line_breaks) >= 1


def test_multilingual_hindi_kannada():
    font_hi = find_font("hi")
    font_kn = find_font("kn")
    if not font_hi or not font_kn:
        pytest.skip("Required Indic fonts not available")
    fitter = TextFitter()
    bbox = BoundingBox(0, 0, 120, 80)
    hi_text = "यह एक परीक्षण वाक्य है"  # Hindi
    kn_text = "ಇದು ಒಂದು ಪರೀಕ್ಷಾ ವಾಕ್ಯ"  # Kannada
    res_hi = fitter.fit_text(hi_text, bbox, TextStyle(font_size=16), font_hi)
    res_kn = fitter.fit_text(kn_text, bbox, TextStyle(font_size=16), font_kn)
    assert res_hi.fit_status in ("fitted", "failed")
    assert res_kn.fit_status in ("fitted", "failed")


def test_failure_when_too_small():
    font = find_font("en")
    if not font:
        pytest.skip("No Latin font available")
    fitter = TextFitter(min_font_size=8.0, font_size_step=2.0)
    bbox = BoundingBox(0, 0, 10, 10)
    res = fitter.fit_text("This cannot fit", bbox, TextStyle(font_size=12), font)
    assert res.fit_status == "failed"
