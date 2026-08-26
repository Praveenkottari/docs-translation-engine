from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable, List, Optional, Sequence, Tuple


class TranslationError(Exception):
    """Generic translation backend error."""


class TranslationBackend(ABC):
    """Abstract translation backend interface.

    Implementations should call `initialize(...)` explicitly before use.
    """

    @abstractmethod
    def initialize(self, model_path: Optional[str] = None, **kwargs) -> None:
        """Initialize the backend (load models from disk)."""

    @abstractmethod
    def translate(self, text: str, source_language: str, target_language: str) -> str:
        """Translate a single string from source_language to target_language.

        Should raise TranslationError for unsupported language pairs.
        """

    def translate_batch(self, texts: Sequence[str], source_language: str, target_language: str) -> List[str]:
        """Default batch implementation using `translate` one-by-one.

        Backends may override with a more efficient bulk API.
        """
        return [self.translate(t, source_language, target_language) for t in texts]


class MockTranslationBackend(TranslationBackend):
    """A deterministic mock translation backend for testing.

    Behavior:
      - `initialize()` must be called before use (simulates model loading).
      - Supports a set of language pairs; if None, supports all pairs.
      - `translate` prepends a deterministic tag to the text: "[src->tgt] " + text
    """

    def __init__(self, supported_pairs: Optional[Iterable[Tuple[str, str]]] = None) -> None:
        self._initialized = False
        self._supported: Optional[set[Tuple[str, str]]] = set(supported_pairs) if supported_pairs is not None else None

    def initialize(self, model_path: Optional[str] = None, **kwargs) -> None:
        # no-op for mock, just mark initialized
        self._initialized = True

    def _check_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError("MockTranslationBackend not initialized. Call initialize() first.")

    def _pair_supported(self, src: str, tgt: str) -> bool:
        if self._supported is None:
            return True
        return (src, tgt) in self._supported

    def translate(self, text: str, source_language: str, target_language: str) -> str:
        self._check_initialized()
        if not self._pair_supported(source_language, target_language):
            raise TranslationError(f"Unsupported language pair: {source_language} -> {target_language}")
        # deterministic behaviour: prefix with pair marker
        return f"[{source_language}->{target_language}] {text}"

    def translate_batch(self, texts: Sequence[str], source_language: str, target_language: str) -> List[str]:
        self._check_initialized()
        if not self._pair_supported(source_language, target_language):
            raise TranslationError(f"Unsupported language pair: {source_language} -> {target_language}")
        return [f"[{source_language}->{target_language}] {t}" for t in texts]
