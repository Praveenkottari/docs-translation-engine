from __future__ import annotations

import os

from PIL import Image, ImageDraw, ImageFont

from odt.processor.scanned_pdf import process_pdf_with_ocr
from odt.ocr.backend import MockOCRBackend

import fitz


def _make_text_pdf(path: str):
    doc = fitz.open()
    page = doc.new_page(width=300, height=200)
    page.insert_text((50, 50), "Native Text PDF", fontsize=12, fontname="Times-Roman")
    doc.save(path)


def _make_scanned_pdf(path: str):
    # create an image with drawn text, then insert image into a PDF page (no native text)
    im = Image.new("RGB", (400, 300), (255, 255, 255))
    draw = ImageDraw.Draw(im)
    draw.text((50, 60), "Scanned Page Text", fill=(0, 0, 0))
    img_path = path + ".png"
    im.save(img_path)

    doc = fitz.open()
    page = doc.new_page(width=400, height=300)
    # insert the image so the PDF page contains only an image
    page.insert_image(fitz.Rect(0, 0, 400, 300), filename=img_path)
    doc.save(path)


def _make_empty_pdf(path: str):
    doc = fitz.open()
    doc.new_page(width=200, height=200)
    doc.save(path)


def test_text_pdf_processing(tmp_path):
    in_pdf = tmp_path / "text.pdf"
    _make_text_pdf(str(in_pdf))

    ocr = MockOCRBackend()
    doc = process_pdf_with_ocr(str(in_pdf), ocr)

    # should retain native text as TextBlock(s)
    assert len(doc.pages) == 1
    page = doc.pages[0]
    texts = [el.text for el in page.elements if hasattr(el, "text")]
    assert any("Native Text PDF" in t for t in texts)


def test_scanned_pdf_processing(tmp_path):
    in_pdf = tmp_path / "scanned.pdf"
    _make_scanned_pdf(str(in_pdf))

    ocr = MockOCRBackend(text="recognized", confidence=0.9)
    doc = process_pdf_with_ocr(str(in_pdf), ocr)

    assert len(doc.pages) == 1
    page = doc.pages[0]

    # first element should be ImageBlock referencing saved image
    assert hasattr(page.elements[0], "image_reference")
    imgref = page.elements[0].image_reference
    assert os.path.exists(imgref)

    # OCR overlay comes after image
    overlays = [el for el in page.elements if getattr(el, "source", None) == "ocr"]
    assert len(overlays) >= 1
    assert any("recognized" in el.text for el in overlays)


def test_empty_pdf_processing(tmp_path):
    in_pdf = tmp_path / "empty.pdf"
    _make_empty_pdf(str(in_pdf))

    ocr = MockOCRBackend()
    doc = process_pdf_with_ocr(str(in_pdf), ocr)

    # empty PDF page: since no native text, will be treated as scanned and produce image + OCR overlay
    assert len(doc.pages) == 1
    page = doc.pages[0]
    assert hasattr(page.elements[0], "image_reference")
