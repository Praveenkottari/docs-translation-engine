Argos Translate integration
==========================

This project supports an offline Argos Translate backend via `ArgosTranslationBackend`.

Installation (offline, local model file)

- Install the Python package into the same Python environment used to run this project:

```bash
python -m pip install --user argostranslate
```

- Obtain Argos model package files (usually with extension `.argosmodel`) from an offline source or the Argos website. Do NOT use the library to download models automatically in CI.

- Install a model package locally (no network) with:

```bash
python -c "from argostranslate import package; package.install_from_path('/path/to/model.argosmodel')"
```

Notes
- `ArgosTranslationBackend.initialize(model_package_path=...)` will call `package.install_from_path()` if a local package path is provided.
- The backend will not perform any automatic downloads or network calls.
