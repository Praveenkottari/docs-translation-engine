from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, List, Optional

from odt.document.models import BoundingBox


@dataclass(frozen=True)
class OCRResult:
    """Normalized OCR result for a single detected text span.

    Attributes:
        text: Extracted text
        bbox: Bounding box in page coordinates (x0,y0,x1,y1)
        confidence: Confidence score between 0.0 and 1.0
        language: Optional language code (e.g. 'en')
        script: Optional script name (e.g. 'Latn')
    """
    text: str
    bbox: BoundingBox
    confidence: float = 1.0
    language: Optional[str] = None
    script: Optional[str] = None


class OCRBackend(ABC):
    """Abstract OCR backend interface.

    Implementations should accept an image-like object (PIL Image, numpy array,
    or a path) to `extract` and return a list of `OCRResult` objects describing
    the detected text and locations.
    """

    @abstractmethod
    def extract(self, image: Any) -> List[OCRResult]:
        """Extract OCR results from `image`.

        `image` is intentionally typed as Any to allow different backends to
        accept different types (PIL.Image, file path, numpy array, etc.).
        """


class MockOCRBackend(OCRBackend):
    """A deterministic mock OCR backend for testing.

    Behavior:
      - If `image` has a `size` attribute (PIL.Image), uses size for bbox.
      - If `image` is a (w,h) tuple, uses that.
      - Otherwise returns a single small bbox and text 'mock'.
    """

    def __init__(self, text: str = "mock", confidence: float = 0.99):
        self._text = text
        self._confidence = float(confidence)

    def extract(self, image: Any) -> List[OCRResult]:
        # Detect image size if available
        width = height = None
        if hasattr(image, "size"):
            try:
                width, height = image.size
            except Exception:
                width = height = None
        elif isinstance(image, (tuple, list)) and len(image) >= 2:
            width, height = int(image[0]), int(image[1])

        if width and height:
            bbox = BoundingBox(0.0, 0.0, float(width), float(height))
        else:
            bbox = BoundingBox(0.0, 0.0, 10.0, 10.0)

        return [OCRResult(text=self._text, bbox=bbox, confidence=self._confidence)]
