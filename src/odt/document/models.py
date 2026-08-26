from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class BoundingBox:
    x0: float
    y0: float
    x1: float
    y1: float

    def __post_init__(self) -> None:
        if self.x1 < self.x0:
            raise ValueError("BoundingBox x1 must be greater than or equal to x0.")
        if self.y1 < self.y0:
            raise ValueError("BoundingBox y1 must be greater than or equal to y0.")

    @property
    def width(self) -> float:
        return self.x1 - self.x0

    @property
    def height(self) -> float:
        return self.y1 - self.y0


@dataclass(frozen=True)
class LanguageInfo:
    code: str
    name: str | None = None
    confidence: float = 1.0
    script: str | None = None

    def __post_init__(self) -> None:
        if not self.code:
            raise ValueError("Language code cannot be empty.")
        if not self.name:
            # default the display name to the code when not supplied
            object.__setattr__(self, "name", self.code)
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("Language confidence must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class TextStyle:
    font_family: str | None = None
    font_size: float | None = None
    bold: bool = False
    italic: bool = False
    underline: bool = False
    color: str | None = None


@dataclass(frozen=True)
class TableCell:
    id: str
    bbox: BoundingBox
    text: str = ""
    row_index: int = 0
    column_index: int = 0
    is_header: bool = False

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("TableCell id cannot be empty.")
        if self.row_index < 0:
            raise ValueError("TableCell row_index must be non-negative.")
        if self.column_index < 0:
            raise ValueError("TableCell column_index must be non-negative.")


@dataclass(frozen=True)
class ImageBlock:
    id: str
    bbox: BoundingBox
    image_reference: str

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("ImageBlock id cannot be empty.")
        if not self.image_reference:
            raise ValueError("ImageBlock image_reference cannot be empty.")


@dataclass(frozen=True)
class TableBlock:
    id: str
    bbox: BoundingBox
    rows: int
    columns: int
    cells: list[list[TableCell]] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("TableBlock id cannot be empty.")
        if self.rows <= 0:
            raise ValueError("TableBlock rows must be positive.")
        if self.columns <= 0:
            raise ValueError("TableBlock columns must be positive.")
        if len(self.cells) != self.rows:
            raise ValueError("TableBlock cell row count does not match declared rows.")
        for row in self.cells:
            if len(row) != self.columns:
                raise ValueError("TableBlock row length does not match declared columns.")


@dataclass(frozen=True)
class TextBlock:
    id: str
    bbox: BoundingBox
    text: str
    language: LanguageInfo | None = None
    confidence: float = 1.0
    style: TextStyle | None = None
    source: str = "ocr"

    def __post_init__(self) -> None:
        if not self.id:
            raise ValueError("TextBlock id cannot be empty.")
        if not self.text and self.source == "ocr":
            raise ValueError("TextBlock text cannot be empty for OCR source.")
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("TextBlock confidence must be between 0.0 and 1.0.")


@dataclass(frozen=True)
class Page:
    width: float
    height: float
    page_number: int
    elements: list[Any] = field(default_factory=list)

    def __post_init__(self) -> None:
        if self.width <= 0:
            raise ValueError("Page width must be positive.")
        if self.height <= 0:
            raise ValueError("Page height must be positive.")
        if self.page_number < 1:
            raise ValueError("Page number must be positive.")


@dataclass(frozen=True)
class Document:
    source_name: str
    pages: list[Page] = field(default_factory=list)
    mime_type: str = "application/octet-stream"
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.source_name:
            raise ValueError("Document source_name cannot be empty.")
        if not self.pages:
            raise ValueError("Document must contain at least one page.")
        page_numbers = [page.page_number for page in self.pages]
        if sorted(page_numbers) != list(range(1, len(page_numbers) + 1)):
            raise ValueError("Document page numbers must be contiguous starting at 1.")
