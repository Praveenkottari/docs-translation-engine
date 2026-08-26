from __future__ import annotations

from odt.document.models import TableBlock, TableCell, BoundingBox
from odt.translation.backend import MockTranslationBackend
from odt.translation.processor import translate_blocks_batched
from odt.lang.detector import SimpleScriptLanguageDetector
from odt.document.models import TextStyle, TextBlock, LanguageInfo


def make_table_2x2():
    # two columns widths preserved
    c0 = 50
    c1 = 200
    w = 600
    # cells: English and Kannada text
    cell00 = TableCell(id="t-r0-c0", bbox=BoundingBox(10, 10, 150, 40), text="Hello", row_index=0, column_index=0, is_header=True, alignment="left")
    cell01 = TableCell(id="t-r0-c1", bbox=BoundingBox(150, 10, 350, 40), text="ನಮಸ್ಕಾರ", row_index=0, column_index=1, is_header=True, alignment="center")
    cell10 = TableCell(id="t-r1-c0", bbox=BoundingBox(10, 40, 150, 80), text="World", row_index=1, column_index=0, is_header=False, alignment="left")
    cell11 = TableCell(id="t-r1-c1", bbox=BoundingBox(150, 40, 350, 80), text="ಹಲೋ", row_index=1, column_index=1, is_header=False, alignment="center")
    rows = [[cell00, cell01], [cell10, cell11]]
    tb = TableBlock(id="t1", bbox=BoundingBox(10, 10, 350, 80), rows=2, columns=2, cells=rows)
    return tb


def test_table_cells_translated_and_geometry_preserved():
    tb = make_table_2x2()
    # flatten cells to TextBlocks
    detector = SimpleScriptLanguageDetector()
    flat = []
    for row in tb.cells:
        for cell in row:
            lang = detector.detect(cell.text)
            flat.append(TextBlock(id=cell.id, bbox=cell.bbox, text=cell.text, language=lang, confidence=1.0, style=TextStyle(), source="ocr"))

    backend = MockTranslationBackend()
    backend.initialize()
    translated = translate_blocks_batched(flat, backend, target_language="en", language_detector=detector)

    # map by id
    byid = {t.id: t for t in translated}
    # verify each cell translated independently and bbox preserved
    for row in tb.cells:
        for cell in row:
            assert cell.id in byid
            t = byid[cell.id]
            assert t.bbox == cell.bbox
            # MockTranslationBackend prefixes translation marker
            assert t.text.startswith("[") and "]" in t.text