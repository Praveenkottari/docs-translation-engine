from __future__ import annotations

from typing import List, Tuple
from statistics import median

from odt.document.models import BoundingBox, TableBlock, TableCell
from odt.ocr.backend import OCRResult


def _yc(envelope: BoundingBox) -> float:
    return (envelope.y0 + envelope.y1) / 2.0


def detect_tables(ocr_results: List[OCRResult], page_width: float, page_height: float) -> List[TableBlock]:
    """Detect simple grid-like tables from OCR results.

    Heuristic approach:
      - cluster OCRResult by row using y-center with adaptive tolerance
      - within rows, note x0 positions of boxes
      - infer columns by aligning x positions across rows
      - require at least 2 rows and 2 columns and reasonable column coverage to accept

    Returns a list of TableBlock objects when detection is reliable; empty list otherwise.
    """
    if not ocr_results:
        return []

    # cluster by row: sort by y-center
    items = sorted(ocr_results, key=lambda r: _yc(r.bbox))
    y_centers = [_yc(r.bbox) for r in items]
    if len(y_centers) < 2:
        return []

    # estimate row tolerance as small fraction of page height or median height
    heights = [r.bbox.height for r in items]
    med_h = median(heights) if heights else max(1.0, page_height * 0.01)
    tol = max(4.0, med_h * 0.75)

    rows: List[List[OCRResult]] = []
    current_row: List[OCRResult] = []
    current_y = None
    for r in items:
        yc = _yc(r.bbox)
        if current_y is None:
            current_y = yc
            current_row = [r]
            rows.append(current_row)
            continue
        if abs(yc - current_y) <= tol:
            current_row.append(r)
        else:
            # start new row
            current_y = yc
            current_row = [r]
            rows.append(current_row)

    # require at least 2 rows
    if len(rows) < 2:
        return []

    # For each row, compute x0 positions of items (left edges)
    row_xs: List[List[float]] = []
    for row in rows:
        xs = sorted([r.bbox.x0 for r in row])
        row_xs.append(xs)

    # infer column boundaries by collecting all x0s and clustering by proximity
    all_xs = sorted({x for xs in row_xs for x in xs})
    if len(all_xs) < 2:
        return []

    # cluster x positions into columns using simple gap threshold
    x_tol = max(6.0, page_width * 0.01)
    columns: List[float] = []
    cur_x = None
    for x in all_xs:
        if cur_x is None:
            cur_x = x
            columns.append(x)
            continue
        if abs(x - cur_x) <= x_tol:
            # skip, same column
            continue
        columns.append(x)
        cur_x = x

    n_rows = len(rows)
    n_cols = len(columns)

    # basic sanity
    if n_rows < 2 or n_cols < 2:
        return []

    # compute coverage: how many rows have at least n_cols items aligned
    aligned_rows = 0
    for row in rows:
        matches = 0
        for col_x in columns:
            # row has item whose x0 within tolerance of col_x
            if any(abs(e.bbox.x0 - col_x) <= x_tol for e in row):
                matches += 1
        if matches >= max(1, n_cols - 1):
            aligned_rows += 1

    coverage = aligned_rows / n_rows
    # accept if most rows align to inferred columns
    if coverage < 0.6:
        return []

    # build cells grid: determine column x positions as boundaries
    # use column left edges and compute right edges from next column or page width
    col_lefts = columns
    col_rights = []
    for i, lx in enumerate(col_lefts):
        if i + 1 < len(col_lefts):
            col_rights.append((lx + col_lefts[i + 1]) / 2.0)
        else:
            col_rights.append(page_width)

    table_cells: List[List[TableCell]] = []
    for r_i, row in enumerate(rows):
        # compute row top/bottom from min y0 and max y1 among items
        top = min(e.bbox.y0 for e in row)
        bottom = max(e.bbox.y1 for e in row)
        row_cells: List[TableCell] = []
        for c_i, (lx, rx) in enumerate(zip(col_lefts, col_rights)):
            # find item overlapping this column
            matched = None
            for e in row:
                # if center x in [lx, rx)
                cx = (e.bbox.x0 + e.bbox.x1) / 2.0
                if lx - x_tol <= cx <= rx + x_tol:
                    matched = e
                    break
            if matched is not None:
                cell_bbox = BoundingBox(matched.bbox.x0, top, matched.bbox.x1, bottom)
                text = matched.text
                # determine alignment by comparing text center to cell center
                cx = (matched.bbox.x0 + matched.bbox.x1) / 2.0
                cell_center = (lx + rx) / 2.0
                # tolerance relative to column width
                col_w = rx - lx if rx > lx else 1.0
                if abs(cx - cell_center) <= max(6.0, col_w * 0.15):
                    alignment = "center"
                elif cx < cell_center:
                    alignment = "left"
                else:
                    alignment = "right"
            else:
                # empty cell bbox based on column/row boundaries
                cell_bbox = BoundingBox(lx, top, rx, bottom)
                text = ""
            cell = TableCell(id=f"t-r{r_i}-c{c_i}", bbox=cell_bbox, text=text, row_index=r_i, column_index=c_i, is_header=(r_i == 0), alignment=alignment if 'alignment' in locals() else 'left')
            row_cells.append(cell)
        table_cells.append(row_cells)

    # compute table bbox as union
    x0 = min(cell.bbox.x0 for row in table_cells for cell in row)
    y0 = min(cell.bbox.y0 for row in table_cells for cell in row)
    x1 = max(cell.bbox.x1 for row in table_cells for cell in row)
    y1 = max(cell.bbox.y1 for row in table_cells for cell in row)
    table_bbox = BoundingBox(x0, y0, x1, y1)

    tb = TableBlock(id="detected-1", bbox=table_bbox, rows=n_rows, columns=n_cols, cells=table_cells)
    return [tb]
