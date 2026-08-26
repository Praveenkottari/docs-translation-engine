from __future__ import annotations

from odt.processor.table_detector import detect_tables
from odt.ocr.backend import OCRResult
from odt.document.models import BoundingBox


def make_ocr_cell(x0, y0, x1, y1, text):
    bbox = BoundingBox(x0, y0, x1, y1)
    return OCRResult(text=text, bbox=bbox, confidence=0.99)


def test_detect_simple_grid_table():
    # construct 3x3 grid OCR results
    cols = [50, 200, 350]
    colw = 120
    rows = [100, 140, 180]
    ocrs = []
    for r_i, ry in enumerate(rows):
        for c_i, cx in enumerate(cols):
            ocrs.append(make_ocr_cell(cx, ry, cx + colw, ry + 20, f"r{r_i}c{c_i}"))

    tables = detect_tables(ocrs, page_width=600, page_height=800)
    assert len(tables) == 1
    t = tables[0]
    assert t.rows == 3
    assert t.columns == 3
    # check cell texts
    for r in range(3):
        for c in range(3):
            assert t.cells[r][c].text == f"r{r}c{c}"
