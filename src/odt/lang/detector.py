from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional, Tuple

from odt.document.models import LanguageInfo


class LanguageDetector(ABC):
    @abstractmethod
    def detect(self, text: str) -> LanguageInfo:
        """Detect the language of the given text and return a LanguageInfo."""


class SimpleScriptLanguageDetector(LanguageDetector):
    """Lightweight detector based on Unicode script ranges.

    This detector counts characters falling into script-specific Unicode ranges
    and returns the script with the most alphabetic characters. It is replaceable
    by a more advanced detector if desired.
    """

    # script -> list of (start, end) ranges (inclusive)
    _SCRIPT_RANGES = {
        "Deva": [(0x0900, 0x097F)],  # Devanagari (Hindi)
        "Taml": [(0x0B80, 0x0BFF)],  # Tamil
        "Telu": [(0x0C00, 0x0C7F)],  # Telugu
        "Knda": [(0x0C80, 0x0CFF)],  # Kannada
        "Mlym": [(0x0D00, 0x0D7F)],  # Malayalam
        # Latin: cover basic Latin and Latin-1 supplement and some extended
        "Latn": [(0x0041, 0x007A), (0x00C0, 0x00FF), (0x0100, 0x017F)],
    }

    _SCRIPT_TO_LANG = {
        "Latn": "en",
        "Deva": "hi",
        "Knda": "kn",
        "Taml": "ta",
        "Telu": "te",
        "Mlym": "ml",
    }

    def _char_script(self, ch: str) -> Optional[str]:
        cp = ord(ch)
        for script, ranges in self._SCRIPT_RANGES.items():
            for start, end in ranges:
                if start <= cp <= end:
                    return script
        return None

    def detect(self, text: str) -> LanguageInfo:
        if not text:
            return LanguageInfo(code="und", name="und", confidence=0.0, script=None)

        total_alpha = 0
        counts: dict[str, int] = {}

        for ch in text:
            if ch.isalpha():
                total_alpha += 1
                script = self._char_script(ch)
                if script:
                    counts[script] = counts.get(script, 0) + 1
                else:
                    # treat ASCII letters as Latin
                    if ord(ch) < 128:
                        counts["Latn"] = counts.get("Latn", 0) + 1

        if total_alpha == 0:
            return LanguageInfo(code="und", name="und", confidence=0.0, script=None)

        # pick script with max count
        best_script, best_count = max(counts.items(), key=lambda kv: kv[1]) if counts else (None, 0)
        confidence = float(best_count) / float(total_alpha) if total_alpha > 0 else 0.0

        lang = self._SCRIPT_TO_LANG.get(best_script, "und") if best_script else "und"
        # use language code as display name for now
        return LanguageInfo(code=lang, name=lang, confidence=confidence, script=best_script)
