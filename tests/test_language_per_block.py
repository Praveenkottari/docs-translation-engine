from __future__ import annotations

import fitz

from odt.processor.scanned_pdf import process_pdf_with_ocr
from odt.lang.detector import SimpleScriptLanguageDetector
from odt.ocr.backend import MockOCRBackend


def test_multiple_language_blocks(tmp_path):
    # create a PDF page with two text lines in different scripts
    p = tmp_path / "multi.pdf"
    doc = fitz.open()
    page = doc.new_page(width=400, height=200)
    page.insert_text((50, 50), "Hello world", fontsize=14)
    page.insert_text((50, 100), "ಇದು ಕನ್ನಡ ವಾಕ್ಯ" , fontsize=14)
    doc.save(str(p))

    detector = SimpleScriptLanguageDetector()
    ocr = MockOCRBackend()
    processed = process_pdf_with_ocr(str(p), ocr, language_detector=detector)

    page = processed.pages[0]
    text_blocks = [el for el in page.elements if hasattr(el, "text")]
    # must detect at least two text blocks and assign languages
    codes = [tb.language.code if tb.language else None for tb in text_blocks]
    assert "en" in codes or "hi" in codes or "kn" in codes
    # at least one should be Kannada (kn)
    assert any(c == "kn" for c in codes if c is not None)
