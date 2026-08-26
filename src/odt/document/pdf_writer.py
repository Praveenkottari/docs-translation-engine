from __future__ import annotations

import os
from typing import Optional

try:
    import fitz  # PyMuPDF
except Exception:  # pragma: no cover - import error surfaces in tests when missing
    fitz = None  # type: ignore

from .models import Document, ImageBlock, Page, TextBlock


def _hex_to_rgb_frac(hex_color: Optional[str]) -> Optional[tuple[float, float, float]]:
    if not hex_color:
        return None
    s = hex_color.lstrip("#")
    if len(s) != 6:
        return None
    r = int(s[0:2], 16) / 255.0
    g = int(s[2:4], 16) / 255.0
    b = int(s[4:6], 16) / 255.0
    return (r, g, b)


def write_document_to_pdf(doc: Document, out_path: str) -> None:
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required to write PDFs")

    pdf = fitz.open()

    for page in doc.pages:
        # create a new page with the same dimensions
        rect = fitz.Rect(0, 0, page.width, page.height)
        p = pdf.new_page(width=rect.width, height=rect.height)

        # iterate elements in order
        for el in page.elements:
            if isinstance(el, TextBlock):
                bb = el.bbox
                r = fitz.Rect(bb.x0, bb.y0, bb.x1, bb.y1)
                style = el.style
                fontsize = style.font_size if (style and style.font_size) else 12
                fontname = style.font_family if (style and style.font_family) else "Times-Roman"
                color = _hex_to_rgb_frac(style.color) if (style and style.color) else None

                # insert text into the bounding rectangle, preserving left alignment
                # Use simple point insertion which is reliably extractable.
                pt = fitz.Point(bb.x0, bb.y0)
                try:
                    if color:
                        p.insert_text(pt, el.text or "", fontsize=fontsize, fontname=fontname, color=color)
                    else:
                        p.insert_text(pt, el.text or "", fontsize=fontsize, fontname=fontname)
                except Exception:
                    # ignore individual text insertion failures
                    pass

            elif isinstance(el, ImageBlock):
                # If the image_reference points to a real file, try to insert it
                img_ref = el.image_reference
                if img_ref and os.path.exists(img_ref):
                    try:
                        img_rect = fitz.Rect(el.bbox.x0, el.bbox.y0, el.bbox.x1, el.bbox.y1)
                        p.insert_image(img_rect, filename=img_ref)
                    except Exception:
                        # ignore failures inserting images
                        pass

    pdf.save(out_path)
    pdf.close()
