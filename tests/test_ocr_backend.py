from __future__ import annotations

from PIL import Image

from odt.ocr.backend import MockOCRBackend, OCRResult


def test_mock_ocr_with_pil_image(tmp_path):
    p = tmp_path / "img.png"
    im = Image.new("RGB", (120, 80), (10, 10, 10))
    im.save(p)

    # reopen and pass the image object
    im2 = Image.open(p)
    backend = MockOCRBackend(text="hello", confidence=0.8)
    results = backend.extract(im2)

    assert isinstance(results, list)
    assert len(results) == 1
    r = results[0]
    assert isinstance(r, OCRResult)
    assert r.text == "hello"
    assert 0.0 <= r.confidence <= 1.0
    assert r.bbox.x1 == 120.0 and r.bbox.y1 == 80.0


def test_mock_ocr_with_size_tuple():
    backend = MockOCRBackend()
    results = backend.extract((10, 20))
    assert len(results) == 1
    r = results[0]
    assert r.bbox.x1 == 10.0
    assert r.bbox.y1 == 20.0
