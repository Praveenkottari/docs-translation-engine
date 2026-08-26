from __future__ import annotations

from typing import List, Optional, Sequence, Tuple

from .backend import TranslationBackend, TranslationError


class ArgosTranslationBackend(TranslationBackend):
    """Adapter for Argos Translate local models (offline only).

    Usage:
      backend = ArgosTranslationBackend()
      backend.initialize(model_package_path="/path/to/model.argosmodel")
      backend.translate("Hello", "en", "es")

    Notes:
      - Requires the `argostranslate` Python package to be installed in the environment.
      - Does not perform any network downloads. If `model_package_path` is given, it
        will install the package from that local file. Otherwise it will use already
        installed Argos packages.
    """

    def __init__(self) -> None:
        self._initialized = False
        self._supported_pairs: set[Tuple[str, str]] = set()
        self._argos_package = None
        self._argos_translate = None

    def initialize(self, model_package_path: Optional[str] = None, **kwargs) -> None:
        try:
            import argostranslate.package as argos_package  # type: ignore
            import argostranslate.translate as argos_translate  # type: ignore
        except Exception as exc:  # pragma: no cover - only when package missing
            raise RuntimeError("Argos Translate package is not installed") from exc

        self._argos_package = argos_package
        self._argos_translate = argos_translate

        # If a local package path is provided, install it (local only)
        if model_package_path:
            # install_from_path will not contact network; it expects a local file
            try:
                argos_package.install_from_path(model_package_path)
            except Exception as exc:  # pragma: no cover - depends on local env
                raise RuntimeError(f"Failed to install Argos model from {model_package_path}: {exc}") from exc

        # Build supported pairs from installed packages
        try:
            installed = argos_package.get_installed_packages()
            for pkg in installed:
                # pkg should expose from_code and to_code
                try:
                    pair = (pkg.from_code, pkg.to_code)
                except Exception:
                    # fallback to attributes that may be named differently
                    pair = (getattr(pkg, "source_language_code", None), getattr(pkg, "target_language_code", None))
                if pair[0] and pair[1]:
                    self._supported_pairs.add(pair)
        except Exception:
            # If introspection failed, leave supported_pairs empty and rely on runtime checks
            self._supported_pairs = set()

        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("ArgosTranslationBackend not initialized; call initialize() first")

    def _pair_supported(self, src: str, tgt: str) -> bool:
        if not self._supported_pairs:
            # no info gathered — assume argos can attempt translation and let it error
            return True
        return (src, tgt) in self._supported_pairs

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        self._check_initialized()
        if not self._pair_supported(source_language, target_language):
            raise TranslationError(f"Unsupported language pair: {source_language} -> {target_language}")
        assert self._argos_translate is not None
        try:
            return self._argos_translate.translate(text, source_language, target_language)
        except Exception as exc:
            raise TranslationError(f"Argos translation failed: {exc}") from exc

    def translate_batch(self, texts: Sequence[str], source_language: str, target_language: str) -> List[str]:
        self._check_initialized()
        if not self._pair_supported(source_language, target_language):
            raise TranslationError(f"Unsupported language pair: {source_language} -> {target_language}")
        # Argos doesn't provide a bulk API; translate one-by-one deterministically
        results: List[str] = []
        for t in texts:
            results.append(self.translate(t, source_language, target_language))
        return results
