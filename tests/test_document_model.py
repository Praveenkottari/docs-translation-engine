from odt.document import (
    BoundingBox,
    Document,
    ImageBlock,
    LanguageInfo,
    Page,
    TableBlock,
    TableCell,
    TextBlock,
    TextStyle,
)


def test_bounding_box_valid_and_geometry() -> None:
    box = BoundingBox(x0=10, y0=20, x1=30, y1=40)

    assert box.width == 20
    assert box.height == 20


def test_bounding_box_rejects_inverted_coordinates() -> None:
    try:
        BoundingBox(x0=50, y0=10, x1=20, y1=30)
        raise AssertionError("Expected ValueError for inverted x coordinates")
    except ValueError:
        pass


def test_language_info_validates_values() -> None:
    info = LanguageInfo(code="en", name="English", confidence=0.92)

    assert info.code == "en"
    assert info.confidence == 0.92

    try:
        LanguageInfo(code="", name="English")
        raise AssertionError("Expected ValueError for empty language code")
    except ValueError:
        pass


def test_text_block_and_page_store_metadata() -> None:
    style = TextStyle(font_family="Arial", font_size=12.0, bold=True)
    text = TextBlock(
        id="t1",
        bbox=BoundingBox(0, 0, 100, 20),
        text="Hello",
        language=LanguageInfo(code="en", name="English"),
        confidence=0.99,
        style=style,
        source="ocr",
    )
    page = Page(width=612, height=792, page_number=1, elements=[text])

    assert page.elements[0] is text
    assert page.elements[0].style is style
    assert page.page_number == 1


def test_document_requires_contiguous_page_numbers() -> None:
    page1 = Page(width=100, height=100, page_number=1)
    page3 = Page(width=100, height=100, page_number=3)

    try:
        Document(source_name="sample.pdf", pages=[page1, page3])
        raise AssertionError("Expected ValueError for non-contiguous page numbers")
    except ValueError:
        pass


def test_table_block_validates_shape() -> None:
    cells = [
        [
            TableCell(
                id="c1",
                bbox=BoundingBox(0, 0, 10, 10),
                text="A",
                row_index=0,
                column_index=0,
            ),
            TableCell(
                id="c2",
                bbox=BoundingBox(10, 0, 20, 10),
                text="B",
                row_index=0,
                column_index=1,
            ),
        ]
    ]
    block = TableBlock(
        id="table-1",
        bbox=BoundingBox(0, 0, 20, 10),
        rows=1,
        columns=2,
        cells=cells,
    )

    assert block.rows == 1
    assert block.columns == 2
    assert block.cells[0][1].text == "B"


def test_image_block_requires_reference() -> None:
    try:
        ImageBlock(id="img-1", bbox=BoundingBox(0, 0, 10, 10), image_reference="")
        raise AssertionError("Expected ValueError for empty image reference")
    except ValueError:
        pass
