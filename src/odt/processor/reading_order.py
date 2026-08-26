from __future__ import annotations

from typing import Iterable, List
from odt.document.models import TextBlock, BoundingBox


def sort_blocks_reading_order(blocks: Iterable[TextBlock], page_width: float, page_height: float) -> List[TextBlock]:
    """Deterministic geometry-based reading order for multi-column pages.

    Algorithm:
      - Identify spanning blocks (width >= 60% of page width).
      - Create horizontal bands using all block y0 and y1 coordinates.
      - Detect column regions by projecting block x-ranges onto discrete bins and finding contiguous covered regions.
      - For each band (top to bottom):
          - emit spanning blocks overlapping the band (left-to-right)
          - for each column left-to-right, emit blocks assigned to that column and overlapping the band (top-to-bottom)

    Returns a new list of blocks in reading order. Coordinates are preserved on blocks.
    """
    blist = list(blocks)
    if not blist:
        return []

    # Determine spanning blocks
    spanning = []
    non_spanning = []
    for b in blist:
        width = b.bbox.x1 - b.bbox.x0
        if width >= 0.6 * page_width:
            spanning.append(b)
        else:
            non_spanning.append(b)

    # Build y bands using all y0 and y1
    ys = sorted({y for b in blist for y in (b.bbox.y0, b.bbox.y1)})
    if len(ys) < 2:
        return sorted(blist, key=lambda b: (b.bbox.y0, b.bbox.x0))

    # detect column regions via projection bins
    nbins = 100
    bins = [0] * nbins
    for b in non_spanning:
        x0 = max(0, min(page_width, b.bbox.x0))
        x1 = max(0, min(page_width, b.bbox.x1))
        i0 = int((x0 / page_width) * nbins)
        i1 = int((x1 / page_width) * nbins)
        i0 = max(0, min(nbins - 1, i0))
        i1 = max(0, min(nbins - 1, i1))
        for i in range(i0, i1 + 1):
            bins[i] = 1

    # find contiguous runs of bins -> columns
    columns = []  # list of (bin_start, bin_end)
    in_run = False
    run_start = 0
    for i, v in enumerate(bins):
        if v and not in_run:
            in_run = True
            run_start = i
        elif not v and in_run:
            in_run = False
            columns.append((run_start, i - 1))
    if in_run:
        columns.append((run_start, len(bins) - 1))

    # convert to x ranges and filter narrow runs
    col_ranges = []
    for a, b in columns:
        x0 = (a / nbins) * page_width
        x1 = ((b + 1) / nbins) * page_width
        if x1 - x0 >= 0.05 * page_width:  # minimal column width
            col_ranges.append((x0, x1))

    # if no columns detected, fallback to single column
    if not col_ranges:
        col_ranges = [(0.0, page_width)]

    # assign non-spanning blocks to columns by center x
    col_assignments = {i: [] for i in range(len(col_ranges))}
    for b in non_spanning:
        cx = (b.bbox.x0 + b.bbox.x1) / 2.0
        assigned = False
        for i, (x0, x1) in enumerate(col_ranges):
            if x0 <= cx <= x1:
                col_assignments[i].append(b)
                assigned = True
                break
        if not assigned:
            # if center outside ranges, assign to nearest column by distance
            dists = [abs(cx - ( (xr[0]+xr[1])/2.0 )) for xr in col_ranges]
            idx = int(min(range(len(dists)), key=lambda k: dists[k]))
            col_assignments[idx].append(b)

    # sort blocks within each column top-to-bottom
    for i in col_assignments:
        col_assignments[i].sort(key=lambda b: (b.bbox.y0, b.bbox.x0))

    # sort spanning blocks left-to-right for stable order
    spanning.sort(key=lambda b: (b.bbox.y0, b.bbox.x0))

    # Build final order by scanning bands
    emitted = set()
    result: List[TextBlock] = []

    for band_start, band_end in zip(ys[:-1], ys[1:]):
        # first spanning blocks overlapping the band
        for s in spanning:
            if s.id in emitted:
                continue
            if s.bbox.y0 < band_end and s.bbox.y1 > band_start:
                result.append(s)
                emitted.add(s.id)

        # for each column left-to-right, emit blocks overlapping the band
        for ci in range(len(col_ranges)):
            for b in col_assignments.get(ci, []):
                if b.id in emitted:
                    continue
                if b.bbox.y0 < band_end and b.bbox.y1 > band_start:
                    result.append(b)
                    emitted.add(b.id)

    # append any remaining blocks not emitted (fallback)
    for b in blist:
        if b.id not in emitted:
            result.append(b)

    return result
