from __future__ import annotations

from typing import Dict, Iterable, List

from odt.document.models import TextBlock, BoundingBox
from odt.font.manager import FontManager
from odt.text.fitter import TextFitter


def render_translated_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    translated_blocks_by_page: Dict[int, Iterable[TextBlock]],
    font_manager: FontManager,
    fitter: TextFitter,
) -> None:
    """Render translated text blocks onto a copy of the input PDF.

    translated_blocks_by_page: mapping page_number (1-based) -> iterable of TextBlock
    Only simple TextBlock objects are supported. The function preserves other page
    content and draws translated text over the original text regions.
    """
    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover - integration tests skip when missing
        raise RuntimeError("pymupdf (fitz) is required for PDF rendering") from exc

    doc = fitz.open(input_pdf_path)

    for page_num, blocks in translated_blocks_by_page.items():
        # page numbers are 1-based in our model
        if page_num < 1 or page_num > len(doc):
            continue
        page = doc[page_num - 1]
        for b in blocks:
            if not isinstance(b, TextBlock):
                continue
            # Convert bbox to fitz.Rect
            r = fitz.Rect(b.bbox.x0, b.bbox.y0, b.bbox.x1, b.bbox.y1)

            # Cover original text: draw a filled rectangle using white background.
            # Note: this may not preserve complex backgrounds; for now it's conservative.
            page.draw_rect(r, color=(1, 1, 1), fill=(1, 1, 1))

            # Choose font for this block
            lang_code = b.language.code if b.language else "und"
            try:
                font_path = font_manager.font_for(lang_code)
            except Exception:
                # fallback to font for Latin
                font_path = font_manager.font_for("en")

            # Fit text into the box
            fit_res = fitter.fit_text(b.text, BoundingBox(r.x0, r.y0, r.x1, r.y1), b.style, font_path)

            # Render text: join line breaks
            render_text = "\n".join(fit_res.line_breaks)

            # insert_textbox: use fontfile to specify font path
            try:
                page.insert_textbox(r, render_text, fontfile=font_path, fontsize=fit_res.font_size, color=(0, 0, 0))
            except Exception:
                # fallback: use default insertion
                page.insert_textbox(r, render_text, fontsize=fit_res.font_size, color=(0, 0, 0))

    doc.save(output_pdf_path)
    doc.close()
