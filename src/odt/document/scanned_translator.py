from __future__ import annotations

from typing import Dict, Iterable
from pathlib import Path
import tempfile

from odt.document.models import TextBlock, BoundingBox, TableBlock, TableCell
from odt.font.manager import FontManager
from odt.text.fitter import TextFitter


def render_translated_scanned_pdf(
    input_pdf_path: str,
    output_pdf_path: str,
    translated_blocks_by_page: Dict[int, Iterable[TextBlock]],
    font_manager: FontManager,
    fitter: TextFitter,
    dpi: int = 150,
) -> None:
    """Render translations onto scanned PDF pages by compositing on the page image.

    For each page with translations:
      - rasterize page to image (deterministic DPI)
      - for each TextBlock: cover region and draw translated text onto the image
      - replace page content with the composed image

    This preserves non-text image content because we start from the page raster.
    """
    try:
        import fitz
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # pragma: no cover - integration skipped when deps missing
        raise RuntimeError("pymupdf and pillow are required for scanned PDF rendering") from exc

    doc = fitz.open(input_pdf_path)
    new_doc = fitz.open()

    scale = dpi / 72.0

    for pno in range(len(doc)):
        page_num = pno + 1
        page = doc[pno]
        rect = page.rect

        if page_num not in translated_blocks_by_page:
            # copy page directly
            new_doc.insert_pdf(doc, from_page=pno, to_page=pno)
            continue

        # rasterize
        pix = page.get_pixmap(matrix=fitz.Matrix(scale, scale), alpha=False)
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        draw = ImageDraw.Draw(img)

        for b in translated_blocks_by_page.get(page_num, []):
            # handle TextBlock
            if isinstance(b, TextBlock):
                # convert bbox to pixel coords
                x0 = int(b.bbox.x0 * scale)
                y0 = int(b.bbox.y0 * scale)
                x1 = int(b.bbox.x1 * scale)
                y1 = int(b.bbox.y1 * scale)

                # cover original region with white rectangle
                draw.rectangle([x0, y0, x1, y1], fill=(255, 255, 255))

                # choose font
                lang_code = b.language.code if b.language else "und"
                try:
                    font_path = font_manager.font_for(lang_code)
                except Exception:
                    font_path = font_manager.font_for("en")

                # target font size in pixels: prefer style.font_size if available (assumed points)
                base_pt = b.style.font_size if (b.style and b.style.font_size) else 12.0
                target_px = base_pt * scale

                # use fitter with pixel bbox
                pixel_bbox = BoundingBox(x0, y0, x1, y1)
                fit_res = fitter.fit_text(b.text, pixel_bbox, b.style, font_path, target_font_size=target_px)

                # draw lines
                lines = fit_res.line_breaks
                # prepare PIL font at fitted size (pixels)
                try:
                    pil_font = ImageFont.truetype(font_path, int(round(fit_res.font_size)))
                except Exception:
                    pil_font = ImageFont.load_default()

                y = y0
                for i, line in enumerate(lines):
                    draw.text((x0, y), line, font=pil_font, fill=(0, 0, 0))
                    # advance by height
                    if i < len(lines) - 1:
                        y += int(round(fit_res.line_spacing + pil_font.getsize(line)[1]))

            # handle TableBlock: render each cell
            elif isinstance(b, TableBlock):
                for row in b.cells:
                    for cell in row:
                        # cell bbox to pixel coords
                        x0 = int(cell.bbox.x0 * scale)
                        y0 = int(cell.bbox.y0 * scale)
                        x1 = int(cell.bbox.x1 * scale)
                        y1 = int(cell.bbox.y1 * scale)

                        # cover original region interior with white rectangle, inset to preserve borders
                        inset = max(2, int(round(min((x1 - x0), (y1 - y0)) * 0.03)))
                        draw.rectangle([x0 + inset, y0 + inset, x1 - inset, y1 - inset], fill=(255, 255, 255))

                        # choose font (treat header differently?)
                        lang_code = "und"
                        try:
                            font_path = font_manager.font_for(lang_code)
                        except Exception:
                            font_path = font_manager.font_for("en")

                        base_pt = 12.0
                        target_px = base_pt * scale

                        pixel_bbox = BoundingBox(x0, y0, x1, y1)
                        fit_res = fitter.fit_text(cell.text, pixel_bbox, None, font_path, target_font_size=target_px)

                        try:
                            pil_font = ImageFont.truetype(font_path, int(round(fit_res.font_size)))
                        except Exception:
                            pil_font = ImageFont.load_default()

                        y = y0 + inset
                        lines = fit_res.line_breaks
                        for i, line in enumerate(lines):
                            # compute x position based on alignment
                            try:
                                line_w = pil_font.getsize(line)[0]
                            except Exception:
                                line_w = 0
                            if cell.alignment == "center":
                                xpos = x0 + (x1 - x0 - line_w) // 2
                            elif cell.alignment == "right":
                                xpos = x1 - inset - line_w
                            else:
                                xpos = x0 + inset

                            draw.text((xpos, y), line, font=pil_font, fill=(0, 0, 0))
                            if i < len(lines) - 1:
                                y += int(round(fit_res.line_spacing + pil_font.getsize(line)[1]))

        # save image to temp PNG and insert into new PDF page
        with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
            tmpname = tf.name
            img.save(tmpname, format="PNG")

        # create new page with same dimensions in points
        new_page = new_doc.new_page(width=rect.width, height=rect.height)
        new_page.insert_image(rect, filename=tmpname)
        # cleanup temp
        try:
            Path(tmpname).unlink()
        except Exception:
            pass

    new_doc.save(output_pdf_path)
    new_doc.close()
    doc.close()
