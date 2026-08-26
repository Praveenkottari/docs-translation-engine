from __future__ import annotations

import os
from typing import Any, Dict, List, Optional

try:
    from paddleocr import PaddleOCR  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    PaddleOCR = None  # type: ignore

from .backend import OCRBackend, OCRResult
from odt.document.models import BoundingBox


class PaddleOCRBackend(OCRBackend):
    """Adapter for PaddleOCR that implements the OCRBackend interface.

    Notes:
    - PaddleOCR is an optional dependency. Importing this module does not
      initialize models. Call `initialize()` explicitly to load model files.
    - Model paths must be provided via `model_paths` to avoid any automatic
      model downloads.
    """

    def __init__(self, model_paths: Optional[Dict[str, str]] = None, lang: str = "en") -> None:
        """Create a backend wrapper.

        Args:
            model_paths: dict that may contain keys `det_model_dir`, `rec_model_dir`,
                and `cls_model_dir`. Paths must point to existing model directories
                extracted from official PaddleOCR releases. If omitted, no models
                are loaded until `initialize()` is called with explicit paths.
            lang: language code passed to PaddleOCR (e.g. 'en', 'ch')
        """
        self._model_paths = model_paths or {}
        self._lang = lang
        self._ocr: Optional[Any] = None

    def initialize(self, model_paths: Optional[Dict[str, str]] = None, use_gpu: bool = False, **kwargs) -> None:
        """Initialize the underlying PaddleOCR instance.

        This must be called explicitly before calling `extract`.

        Args:
            model_paths: same shape as constructor; overrides stored paths.
            use_gpu: whether to enable GPU in PaddleOCR.
            **kwargs: forwarded to PaddleOCR constructor.
        """
        if PaddleOCR is None:
            raise ImportError("paddleocr is required for PaddleOCRBackend; install it separately")

        if model_paths:
            self._model_paths.update(model_paths)

        # Validate provided model paths: do not attempt downloads
        det = self._model_paths.get("det_model_dir")
        rec = self._model_paths.get("rec_model_dir")
        cls = self._model_paths.get("cls_model_dir")

        if det is not None and not os.path.exists(det):
            raise FileNotFoundError(f"det_model_dir not found: {det}")
        if rec is not None and not os.path.exists(rec):
            raise FileNotFoundError(f"rec_model_dir not found: {rec}")
        if cls is not None and not os.path.exists(cls):
            raise FileNotFoundError(f"cls_model_dir not found: {cls}")

        # Initialize PaddleOCR with explicit model dirs when provided
        ocr_kwargs: Dict[str, Any] = dict(lang=self._lang, use_angle_cls=False, use_gpu=use_gpu)
        # pass model dirs if present
        if det:
            ocr_kwargs["det_model_dir"] = det
        if rec:
            ocr_kwargs["rec_model_dir"] = rec
        if cls:
            ocr_kwargs["cls_model_dir"] = cls

        ocr_kwargs.update(kwargs)
        self._ocr = PaddleOCR(**ocr_kwargs)

    def extract(self, image: Any) -> List[OCRResult]:
        if self._ocr is None:
            raise RuntimeError("PaddleOCRBackend not initialized. Call initialize() with model paths first.")

        # paddleocr accepts file paths or numpy arrays or PIL Images
        raw = self._ocr.ocr(image, cls=False)

        results: List[OCRResult] = []
        for page_or_line in raw:
            # PaddleOCR returns list of lines: each is [bbox, (text, score)]
            try:
                bbox_pts, (text, score) = page_or_line
            except Exception:
                continue

            # bbox_pts is list of 4 points [[x1,y1], ...]
            xs = [float(p[0]) for p in bbox_pts]
            ys = [float(p[1]) for p in bbox_pts]
            x0, x1 = min(xs), max(xs)
            y0, y1 = min(ys), max(ys)
            bb = BoundingBox(x0, y0, x1, y1)
            conf = float(score) if score is not None else 1.0
            results.append(OCRResult(text=text, bbox=bb, confidence=conf))

        return results
