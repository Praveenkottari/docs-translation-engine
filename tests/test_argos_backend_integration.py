from __future__ import annotations

import pytest

try:
    import argostranslate.package as argos_package  # type: ignore
    import argostranslate.translate as argos_translate  # type: ignore
except Exception:  # pragma: no cover - skip when not installed
    argos_package = None  # type: ignore
    argos_translate = None  # type: ignore

from odt.translation.argos_backend import ArgosTranslationBackend


pytestmark = pytest.mark.skipif(argos_package is None, reason="argostranslate not installed")


def test_argos_backend_runs_if_models_installed(tmp_path):
    # Skip if no installed packages
    installed = argos_package.get_installed_packages()
    if not installed:
        pytest.skip("No Argos models installed locally; skipping integration test")

    backend = ArgosTranslationBackend()
    backend.initialize()

    # pick a supported pair from installed packages
    pkg = installed[0]
    src = getattr(pkg, "from_code", getattr(pkg, "source_language_code", None))
    tgt = getattr(pkg, "to_code", getattr(pkg, "target_language_code", None))
    if not src or not tgt:
        pytest.skip("Unable to determine language codes from installed Argos package")

    res = backend.translate("Hello world", src, tgt)
    assert isinstance(res, str) and len(res) > 0
