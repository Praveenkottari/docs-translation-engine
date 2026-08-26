from __future__ import annotations

import os
from typing import Optional

try:
    from PIL import Image
except Exception:  # pragma: no cover - import error reported by tests when missing
    Image = None  # type: ignore

from .models import BoundingBox, Document, ImageBlock, Page


def read_image_to_document(path: str) -> Document:
    """Read an image file (PNG/JPEG) and convert it to a one-page Document.

    The returned Document contains a single Page whose dimensions match the
    image pixel dimensions and one `ImageBlock` covering the full page with
    `image_reference` pointing to the original path.
    """
    if Image is None:
        raise ImportError("Pillow (PIL) is required to read images")

    if not os.path.exists(path):
        raise FileNotFoundError(path)

    with Image.open(path) as im:
        width, height = im.size  # (width, height)

    # Use float page dimensions matching pixel dimensions
    bbox = BoundingBox(0.0, 0.0, float(width), float(height))
    image_block = ImageBlock(id="img-1", bbox=bbox, image_reference=path)

    page = Page(width=float(width), height=float(height), page_number=1, elements=[image_block])
    doc = Document(source_name=os.path.basename(path) or path, pages=[page], mime_type="image/*", metadata={})
    return doc
