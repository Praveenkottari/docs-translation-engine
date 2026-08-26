from __future__ import annotations

import os

from PIL import Image

from odt.document.image_reader import read_image_to_document


def _make_image(path: str, size=(128, 64), color=(200, 100, 50)):
    im = Image.new("RGB", size, color)
    im.save(path)


def test_read_png(tmp_path):
    p = tmp_path / "test.png"
    _make_image(str(p), size=(200, 100), color=(10, 20, 30))

    doc = read_image_to_document(str(p))
    assert len(doc.pages) == 1
    page = doc.pages[0]
    assert page.width == 200.0
    assert page.height == 100.0

    # contains exactly one ImageBlock element
    imgs = [el for el in page.elements if hasattr(el, "image_reference")]
    assert len(imgs) == 1
    ib = imgs[0]
    assert ib.image_reference == str(p)
    assert ib.bbox.x0 == 0.0 and ib.bbox.y0 == 0.0
    assert ib.bbox.x1 == 200.0 and ib.bbox.y1 == 100.0


def test_read_jpeg(tmp_path):
    p = tmp_path / "test.jpg"
    _make_image(str(p), size=(320, 240), color=(255, 255, 0))

    doc = read_image_to_document(str(p))
    page = doc.pages[0]
    assert page.width == 320.0
    assert page.height == 240.0
