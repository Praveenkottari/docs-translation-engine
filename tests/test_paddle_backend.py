from __future__ import annotations

import os
import pytest

from odt.ocr.paddle import PaddleOCRBackend


PADDLE_DET = os.environ.get("PADDLE_DET_MODEL_DIR")
PADDLE_REC = os.environ.get("PADDLE_REC_MODEL_DIR")


@pytest.mark.skipif(not (PADDLE_DET and PADDLE_REC), reason="PaddleOCR model dirs not provided")
def test_paddle_backend_integration(tmp_path):
    # This is an integration test that runs only when model dirs are provided
    inp = tmp_path / "img.png"
    # create a small blank image to feed engine
    from PIL import Image

    Image.new("RGB", (100, 50), (255, 255, 255)).save(inp)

    backend = PaddleOCRBackend(model_paths={"det_model_dir": PADDLE_DET, "rec_model_dir": PADDLE_REC}, lang="en")
    backend.initialize()
    results = backend.extract(str(inp))

    # we expect zero or more results; ensure returned objects are of expected type
    assert isinstance(results, list)
    for r in results:
        assert hasattr(r, "text")
        assert hasattr(r, "bbox")
        assert 0.0 <= r.confidence <= 1.0
