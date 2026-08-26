3rd-party components and licenses

PaddleOCR
---------
- Package: paddleocr
- License: Apache-2.0
- Notes: PaddleOCR is an optional component. The project does not download
  model files automatically. Users must obtain PaddleOCR model files and
  provide their paths via environment variables or configuration.

Installation & model requirements
---------------------------------
- Install the Python package: `pip install paddleocr` (choose a suitable
  version compatible with your environment).
- Model files: download the official PaddleOCR model archive(s) and extract
  them. Provide the model directories to the `PaddleOCRBackend.initialize()`
  call via `det_model_dir` and `rec_model_dir` keys. The integration tests
  will only run if these environment variables are set:
    - `PADDLE_DET_MODEL_DIR`
    - `PADDLE_REC_MODEL_DIR`

Please update this file with the exact `paddleocr` version you used and any
attribution details required by your organization's licensing policies.
# Third-Party Licenses

This project currently has no runtime dependencies beyond the Python standard library and the development tools used for testing and linting.

When model, OCR, translation, or rendering backends are added later, their licensing information must be reviewed and recorded here before those dependencies are incorporated into the project.

Argos Translate
---------------
- Package: argostranslate
- Purpose: Offline neural machine translation package used via `ArgosTranslationBackend`.
- Installation: `python -m pip install --user argostranslate` (or install into your environment of choice).
- Models: Argos uses local `.argosmodel` files which must be obtained and installed locally via `argostranslate.package.install_from_path()`; this project does not download models automatically.
- License: Please record the exact package and model license information (and version) here after installation. You can query the installed package version with:

```bash
python -c "import importlib.metadata as m; print(m.version('argostranslate'))"
```

Note: Model files themselves may have separate licensing and attribution requirements; ensure these are recorded here as well when you add them to the project.
