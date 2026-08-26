from __future__ import annotations

import os
from typing import Optional

try:
    import fitz  # PyMuPDF
except Exception as exc:  # pragma: no cover - import error surfaces in tests when missing
    fitz = None  # type: ignore

from .models import (
    BoundingBox,
    Document,
    ImageBlock,
    Page,
    TextBlock,
    TextStyle,
)


def _convert_color(color: Optional[object]) -> Optional[str]:
    if color is None:
        return None
    # PyMuPDF may return an int like 0xRRGGBB
    if isinstance(color, int):
        rgb = color & 0xFFFFFF
        return "#{:06x}".format(rgb)
    # Or a tuple/list: either 0-1 floats or 0-255 ints
    if isinstance(color, (list, tuple)) and len(color) >= 3:
        r, g, b = color[0], color[1], color[2]
        if isinstance(r, float) and 0.0 <= r <= 1.0:
            r, g, b = int(r * 255), int(g * 255), int(b * 255)
        return "#{:02x}{:02x}{:02x}".format(int(r), int(g), int(b))
    return str(color)


def read_pdf_to_document(path: str) -> Document:
    """Read a PDF file at ``path`` and convert it into the internal `Document` model.

    Notes:
    - Does not perform OCR or translation.
    - Preserves page order and block ordering as reported by PyMuPDF.
    - Extracts text spans, bbox, font name, font size, and text color when available.
    - Emits image references for image blocks.
    """
    if fitz is None:
        raise ImportError("PyMuPDF (fitz) is required to read PDFs")

    src_name = os.path.basename(path) or path
    pdf = fitz.open(path)
    pages: list[Page] = []

    for p_i in range(pdf.page_count):
        page = pdf.load_page(p_i)
        rect = page.rect
        width, height = float(rect.width), float(rect.height)
        elements: list[object] = []

        # Use the "dict" text extractor to preserve block/line/span ordering
        text_dict = page.get_text("dict")
        for b_i, block in enumerate(text_dict.get("blocks", [])):
            btype = block.get("type", 0)
            if btype == 0:  # text block
                for l_i, line in enumerate(block.get("lines", [])):
                    for s_i, span in enumerate(line.get("spans", [])):
                        bbox = span.get("bbox", (0.0, 0.0, 0.0, 0.0))
                        bb = BoundingBox(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                        font = span.get("font")
                        size = float(span.get("size", 0.0)) if span.get("size") is not None else None
                        color = _convert_color(span.get("color"))

                        fname = font if font else None
                        # best-effort bold/italic detection from font name
                        bold = bool(fname and ("Bold" in fname or "BD" in fname))
                        italic = bool(fname and ("Italic" in fname or "Oblique" in fname))

                        style = TextStyle(font_family=fname, font_size=size, bold=bold, italic=italic, color=color)

                        tb = TextBlock(
                            id=f"p{p_i+1}-b{b_i}-l{l_i}-s{s_i}",
                            bbox=bb,
                            text=span.get("text", ""),
                            language=None,
                            confidence=1.0,
                            style=style,
                            source="native",
                        )
                        elements.append(tb)
            elif btype == 1:  # image block
                bbox = block.get("bbox", (0.0, 0.0, 0.0, 0.0))
                bb = BoundingBox(float(bbox[0]), float(bbox[1]), float(bbox[2]), float(bbox[3]))
                img_ref = f"{src_name}#image-{p_i+1}-{b_i}"
                ib = ImageBlock(id=f"p{p_i+1}-img{b_i}", bbox=bb, image_reference=img_ref)
                elements.append(ib)

        pages.append(Page(width=width, height=height, page_number=p_i + 1, elements=elements))

    return Document(source_name=src_name, pages=pages, mime_type="application/pdf", metadata={})
