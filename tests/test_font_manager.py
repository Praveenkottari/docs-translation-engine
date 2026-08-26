from __future__ import annotations

import os
from pathlib import Path

import pytest

from odt.font.manager import FontManager, FontNotFoundError


def write_dummy_font(p: Path) -> None:
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_bytes(b"")


def test_select_devanagari_font(tmp_path: Path):
    d = tmp_path / "fonts"
    f = d / "NotoSansDevanagari-Regular.ttf"
    write_dummy_font(f)

    fm = FontManager(font_dirs=[str(d)])
    selected = fm.font_for("hi")
    assert selected.endswith("NotoSansDevanagari-Regular.ttf")


def test_select_latin_font(tmp_path: Path):
    d = tmp_path / "f2"
    f = d / "DejaVuSans.ttf"
    write_dummy_font(f)
    fm = FontManager(font_dirs=[str(d)])
    selected = fm.font_for("en")
    assert selected.endswith("DejaVuSans.ttf")


def test_deterministic_fallback_order(tmp_path: Path):
    d1 = tmp_path / "a"
    d2 = tmp_path / "b"
    f1 = d1 / "somefont.ttf"
    f2 = d2 / "otherfont.ttf"
    write_dummy_font(f1)
    write_dummy_font(f2)
    # manager searches directories in given order
    fm = FontManager(font_dirs=[str(d2), str(d1)])
    sel = fm.font_for("en")
    assert sel.endswith("otherfont.ttf")


def test_no_fonts_error(tmp_path: Path):
    fm = FontManager(font_dirs=[str(tmp_path / "empty")])
    with pytest.raises(FontNotFoundError):
        fm.font_for("kn")
