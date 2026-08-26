from __future__ import annotations

import argparse
import os
import sys

from typing import Optional

from .document.pdf_reader import read_pdf_to_document
from .document.pdf_writer import write_document_to_pdf
from .processor.scanned_pdf import process_pdf_with_ocr
from .document.pdf_translator import render_translated_pdf
from .document.scanned_translator import render_translated_scanned_pdf
from .lang.detector import SimpleScriptLanguageDetector
from .translation.backend import MockTranslationBackend
from .ocr.backend import MockOCRBackend
from .translation.processor import translate_blocks_batched
from .font.manager import FontManager
from .text.fitter import TextFitter
from typing import List
from .document.image_reader import read_image_to_document
from PIL import Image
import tempfile


def _error(msg: str) -> None:
    print(f"Error: {msg}", file=sys.stderr)


def roundtrip_command(input_path: str, output_path: str) -> int:
    # validate input
    if not os.path.exists(input_path):
        _error(f"Input file does not exist: {input_path}")
        return 2
    if not os.path.isfile(input_path):
        _error(f"Input path is not a file: {input_path}")
        return 2

    out_dir = os.path.dirname(output_path) or os.getcwd()
    if out_dir and not os.path.exists(out_dir):
        try:
            os.makedirs(out_dir, exist_ok=True)
        except Exception as exc:
            _error(f"Cannot create output directory {out_dir}: {exc}")
            return 3

    try:
        doc = read_pdf_to_document(input_path)
    except Exception as exc:
        _error(f"Failed to read PDF: {exc}")
        return 4

    try:
        write_document_to_pdf(doc, output_path)
    except Exception as exc:
        _error(f"Failed to write PDF: {exc}")
        return 5

    print(f"Wrote: {output_path}")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(prog="odt")
    sub = parser.add_subparsers(dest="command")

    rp = sub.add_parser("roundtrip", help="Read PDF into Document and write back")
    rp.add_argument("input", help="Input PDF path")
    rp.add_argument("--output", "-o", required=True, help="Output PDF path")

    p_tr = sub.add_parser("translate", help="Translate the document")
    p_tr.add_argument("input", help="Input document path")
    p_tr.add_argument("--target", required=True, help="Target language for translation")
    p_tr.add_argument("--output", required=True, help="Output translated document path")

    args = parser.parse_args(argv)
    if args.command == "roundtrip":
        return roundtrip_command(args.input, args.output)

    if args.command == "translate":
        # validate input
        input_path = args.input
        output_path = args.output
        target = args.target

        # basic target validation
        allowed = set(SimpleScriptLanguageDetector._SCRIPT_TO_LANG.values())
        if target not in allowed:
            _error(f"Unsupported target language: {target}")
            return 2

        if not os.path.exists(input_path) or not os.path.isfile(input_path):
            _error(f"Input file not found: {input_path}")
            return 2

        out_dir = os.path.dirname(output_path) or os.getcwd()
        if out_dir and not os.path.exists(out_dir):
            try:
                os.makedirs(out_dir, exist_ok=True)
            except Exception as exc:
                _error(f"Cannot create output directory {out_dir}: {exc}")
                return 3

        print("Detecting document type and extracting text...")
        # process PDF: use OCR where necessary
        detector = SimpleScriptLanguageDetector()
        ocr_backend = MockOCRBackend()

        try:
            # This returns a Document with native text blocks or image+ocr overlays
            doc = process_pdf_with_ocr(input_path, ocr_backend=ocr_backend, language_detector=detector)
        except Exception as exc:
            _error(f"Failed to process PDF: {exc}")
            return 4

            # If input is an image, run OCR and create a document
            image_exts = (".png", ".jpg", ".jpeg")
            if input_path.lower().endswith(image_exts):
                print("Input is an image; running OCR and building document model...")
                try:
                    img_doc = read_image_to_document(input_path)
                    # run OCR on the image
                    pil_im = Image.open(input_path)
                    ocr_results = ocr_backend.extract(pil_im)
                    # convert OCR results to TextBlocks and attach to page
                    from odt.document.models import TextBlock, TextStyle

                    elements = [el for el in img_doc.pages[0].elements]
                    for s_i, res in enumerate(ocr_results):
                        tb = TextBlock(
                            id=f"img-ocr{s_i}",
                            bbox=res.bbox,
                            text=res.text,
                            language=detector.detect(res.text),
                            confidence=res.confidence,
                            style=TextStyle(font_family=None, font_size=None, color=None),
                            source="ocr",
                        )
                        elements.append(tb)
                    img_doc.pages[0].elements = elements  # type: ignore[attr-defined]
                    doc = img_doc
                except Exception as exc:
                    _error(f"Failed to process image: {exc}")
                    return 4

        print("Translating text blocks (batched)...")
        fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/usr/share/fonts", os.path.expanduser("~/.local/share/fonts")])
        fitter = TextFitter()

        # For each page, collect TextBlocks and translate in batched groups
        translated_by_page = {}
        from odt.document.models import TextBlock, ImageBlock, TableBlock, TableCell

        for page in doc.pages:
            page_texts = [el for el in page.elements if isinstance(el, TextBlock)]
            page_tables = [el for el in page.elements if isinstance(el, TableBlock)]

            # prepare flat list of TextBlock-like objects for translation: include page_texts and each table cell as TextBlock
            flat_blocks = []
            cell_parent = {}
            for tb in page_texts:
                flat_blocks.append(tb)
            for table in page_tables:
                for row in table.cells:
                    for cell in row:
                        # create ephemeral TextBlock for cell
                        from odt.document.models import TextStyle, LanguageInfo
                        ephemeral = TextBlock(id=cell.id, bbox=cell.bbox, text=cell.text, language=LanguageInfo(code="und"), confidence=1.0, style=TextStyle(), source="ocr")
                        flat_blocks.append(ephemeral)
                        cell_parent[ephemeral.id] = (table, cell.row_index, cell.column_index)

            if not flat_blocks:
                continue

            backend = MockTranslationBackend()
            backend.initialize()
            translated_flat = translate_blocks_batched(flat_blocks, backend, target, language_detector=detector)

            # Assemble translated page elements: map back translations
            translated_elements = []
            # first, create a dict for translated texts by id
            trans_by_id = {tb.id: tb for tb in translated_flat}

            # keep non-text elements like ImageBlock
            for el in page.elements:
                if isinstance(el, ImageBlock):
                    translated_elements.append(el)
                elif isinstance(el, TableBlock):
                    # rebuild table with translated cell texts
                    new_cells = []
                    for r_i, row in enumerate(el.cells):
                        new_row = []
                        for c_i, cell in enumerate(row):
                            tb_id = cell.id
                            if tb_id in trans_by_id:
                                new_text = trans_by_id[tb_id].text
                            else:
                                new_text = cell.text
                                    new_cell = TableCell(id=cell.id, bbox=cell.bbox, text=new_text, row_index=cell.row_index, column_index=cell.column_index, is_header=cell.is_header, alignment=cell.alignment)
                            new_row.append(new_cell)
                        new_cells.append(new_row)
                    translated_table = TableBlock(id=el.id, bbox=el.bbox, rows=el.rows, columns=el.columns, cells=new_cells)
                    translated_elements.append(translated_table)
                elif isinstance(el, TextBlock):
                    # replace with translated version if present
                    if el.id in trans_by_id:
                        translated_elements.append(trans_by_id[el.id])
                    else:
                        translated_elements.append(el)
                else:
                    translated_elements.append(el)

            translated_by_page[page.page_number] = translated_elements

            # If input was image, create a temp PDF with the image to render scanned pipeline
            temp_pdf = None
            if input_path.lower().endswith(image_exts):
                try:
                    tmpf = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
                    tmpf.close()
                    # Save image as single-page PDF
                    im = Image.open(input_path).convert("RGB")
                    im.save(tmpf.name, format="PDF")
                    temp_pdf = tmpf.name
                    input_for_render = temp_pdf
                except Exception as exc:
                    _error(f"Failed to create temp PDF from image: {exc}")
                    return 5
            else:
                input_for_render = input_path

        print("Rendering translated PDF (native/scanned pages)...")
        try:
            # Separate pages by scanned/native: detect if page has an ImageBlock
            has_scanned = any(any(isinstance(el, ImageBlock) for el in p.elements) for p in doc.pages)
            if has_scanned:
                if has_scanned or input_path.lower().endswith(image_exts):
                    render_translated_scanned_pdf(input_for_render, output_path, translated_by_page, fm, fitter)
                else:
                    render_translated_pdf(input_for_render, output_path, translated_by_page, fm, fitter)
        except Exception as exc:
            _error(f"Failed to render translated PDF: {exc}")
            return 6

        print(f"Wrote translated PDF: {output_path}")
            # cleanup temp pdf if created
            if temp_pdf:
                try:
                    os.unlink(temp_pdf)
                except Exception:
                    pass
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
