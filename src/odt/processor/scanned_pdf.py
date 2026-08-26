from __future__ import annotations

import os
import tempfile
from typing import Optional

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - import error
    fitz = None  # type: ignore

from PIL import Image

from odt.document.pdf_reader import read_pdf_to_document
from odt.document.image_reader import read_image_to_document
from odt.document.models import BoundingBox, Document, ImageBlock, Page, TextBlock, TextStyle
from odt.ocr.backend import OCRBackend
from odt.lang.detector import LanguageDetector, SimpleScriptLanguageDetector
from odt.processor.table_detector import detect_tables
from odt.document.models import TableBlock



def process_pdf_with_ocr(path: str, ocr_backend: OCRBackend, image_out_dir: Optional[str] = None, language_detector: Optional[LanguageDetector] = None) -> Document:
    """Process a PDF: use native text when available, otherwise render page to image and OCR.

    For scanned pages the original page image is saved to `image_out_dir` (created
    automatically if not provided) and included in the returned `Document` as an
    `ImageBlock`. OCR results are returned as overlay `TextBlock`s.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required for PDF processing")

    if image_out_dir is None:
        image_out_dir = tempfile.mkdtemp(prefix="odt_page_images_")
    os.makedirs(image_out_dir, exist_ok=True)

    # Helper to save a page image and return path
    def _save_page_image(page: fitz.Page, page_index: int) -> str:
        pix = page.get_pixmap(alpha=False)
        out_path = os.path.join(image_out_dir, f"{os.path.basename(path)}-p{page_index+1}.png")
        pix.save(out_path)
        return out_path

    doc_pages: list[Page] = []
    pdf = fitz.open(path)

    # Use pdf_reader for native extraction when possible
    native_doc = read_pdf_to_document(path)

    # We'll map native_doc pages by page_number for reuse
    native_pages_by_num = {p.page_number: p for p in native_doc.pages}

    for p_i in range(pdf.page_count):
        page = pdf.load_page(p_i)
        # simple heuristic: if native page text has any non-empty text, treat as native
        native_page = native_pages_by_num.get(p_i + 1)
        has_native_text = False
        if native_page:
            # check if any TextBlock exists with non-empty text
            for el in native_page.elements:
                if isinstance(el, TextBlock) and el.text and el.text.strip():
                    has_native_text = True
                    break

        if has_native_text:
            # annotate native page TextBlocks with language if detector provided
            elements: list = []
            for el in native_page.elements:
                if isinstance(el, TextBlock):
                    if language_detector is not None:
                        lang = language_detector.detect(el.text)
                    else:
                        lang = None
                    # recreate TextBlock with language set
                    new_tb = TextBlock(
                        id=el.id,
                        bbox=el.bbox,
                        text=el.text,
                        language=lang,
                        confidence=el.confidence,
                        style=el.style,
                        source=el.source,
                    )
                    elements.append(new_tb)
                else:
                    elements.append(el)
            page_model = Page(width=native_page.width, height=native_page.height, page_number=native_page.page_number, elements=elements)
            doc_pages.append(page_model)
            continue

        # Scanned page: render to image, save image, OCR, and convert OCR results
        img_path = _save_page_image(page, p_i)
        # feed PIL image or path to OCR backend
        # Many OCR backends accept file paths; MockOCRBackend accepts PIL.Image or tuple.
        pil_im = Image.open(img_path)
        ocr_results = ocr_backend.extract(pil_im)

        # Create ImageBlock for the original page image
        width, height = pil_im.size
        img_bbox = BoundingBox(0.0, 0.0, float(width), float(height))
        image_block = ImageBlock(id=f"p{p_i+1}-origimg", bbox=img_bbox, image_reference=img_path)

        elements: list = [image_block]

        # Convert OCRResult objects to TextBlock overlay objects
        ocr_textblocks = []
        for s_i, res in enumerate(ocr_results):
            if language_detector is not None:
                lang = language_detector.detect(res.text)
            else:
                lang = None

            tb = TextBlock(
                id=f"p{p_i+1}-ocr{s_i}",
                bbox=res.bbox,
                text=res.text,
                language=lang,
                confidence=res.confidence,
                style=TextStyle(font_family=None, font_size=None, color=None),
                source="ocr",
            )
            ocr_textblocks.append(tb)

        # Attempt to detect tables from OCR results; only include TableBlock if detection reliable
        tables: list[TableBlock] = []
        try:
            detected = detect_tables(ocr_results, float(width), float(height))
            if detected:
                tables = detected
        except Exception:
            tables = []

        # add image block + either table blocks or text blocks
        if tables:
            elements.extend(tables)
        else:
            elements.extend(ocr_textblocks)

        page_model = Page(width=float(width), height=float(height), page_number=p_i + 1, elements=elements)
        doc_pages.append(page_model)

    return Document(source_name=os.path.basename(path) or path, pages=doc_pages, mime_type="application/pdf", metadata={})
