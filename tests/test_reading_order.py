from __future__ import annotations

from odt.processor.reading_order import sort_blocks_reading_order
from odt.document.models import TextBlock, BoundingBox, TextStyle, LanguageInfo


def make_tb(id, x0, y0, x1, y1, text):
    return TextBlock(id=id, bbox=BoundingBox(x0, y0, x1, y1), text=text, language=LanguageInfo(code="en"), confidence=1.0, style=TextStyle(), source="ocr")


def test_one_column_order():
    w = 600
    # three blocks stacked top to bottom
    a = make_tb("a", 50, 10, 550, 40, "A")
    b = make_tb("b", 50, 50, 550, 80, "B")
    c = make_tb("c", 50, 90, 550, 120, "C")
    out = sort_blocks_reading_order([b, c, a], page_width=w, page_height=800)
    assert [t.id for t in out] == ["a", "b", "c"]


def test_two_column_order():
    w = 600
    # left column x approx 50-270, right column 310-530
    l1 = make_tb("l1", 50, 10, 270, 40, "L1")
    l2 = make_tb("l2", 50, 50, 270, 80, "L2")
    r1 = make_tb("r1", 330, 10, 530, 40, "R1")
    r2 = make_tb("r2", 330, 50, 530, 80, "R2")
    out = sort_blocks_reading_order([r1, l2, r2, l1], page_width=w, page_height=800)
    # expect left column top-bottom, then right column top-bottom
    assert [t.id for t in out] == ["l1", "l2", "r1", "r2"]


def test_three_column_order():
    w = 600
    c1 = make_tb("c1", 10, 10, 170, 30, "C1")
    c2 = make_tb("c2", 190, 10, 350, 30, "C2")
    c3 = make_tb("c3", 370, 10, 560, 30, "C3")
    c1b = make_tb("c1b", 10, 40, 170, 60, "C1b")
    c2b = make_tb("c2b", 190, 40, 350, 60, "C2b")
    c3b = make_tb("c3b", 370, 40, 560, 60, "C3b")
    out = sort_blocks_reading_order([c2, c3b, c1b, c1, c2b, c3], page_width=w, page_height=800)
    assert [t.id for t in out] == ["c1", "c1b", "c2", "c2b", "c3", "c3b"]


def test_heading_spanning_columns():
    w = 600
    heading = make_tb("h", 10, 5, 590, 30, "Heading")
    l1 = make_tb("l1", 50, 40, 270, 70, "L1")
    r1 = make_tb("r1", 330, 40, 530, 70, "R1")
    out = sort_blocks_reading_order([l1, heading, r1], page_width=w, page_height=800)
    # heading should come first, then columns left->right
    assert [t.id for t in out] == ["h", "l1", "r1"]
