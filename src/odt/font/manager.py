from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, List


class FontNotFoundError(FileNotFoundError):
    pass


class FontManager:
    """Select fonts capable of rendering a given language or script.

    The manager searches configured font directories for candidate font files
    (ttf/otf/ttc). Selection is based on filename heuristics (preferred name
    substrings per script). This avoids introducing heavy font-parsing
    dependencies while remaining deterministic and configurable.

    Usage:
      fm = FontManager(font_dirs=["/usr/share/fonts", "/home/user/.local/share/fonts"])
      path = fm.font_for("hi")  # Hindi -> Devanagari script
    """

    # Map language codes to script keys
    LANG_TO_SCRIPT = {
        "en": "Latn",
        "hi": "Deva",
        "kn": "Knda",
        "ta": "Taml",
        "te": "Telu",
        "ml": "Mlym",
    }

    # Preferred filename substrings per script (ordered). Case-insensitive.
    PREFERRED = {
        "Latn": ["notosans", "dejavusans", "liberationsans", "arial", "timesnewroman"],
        "Deva": ["notosansdevanagari", "notosans-devanagari", "lohitdevanagari", "mangal", "devanagari"],
        "Knda": ["notosanskannada", "notosans-kannada", "lohittamil", "lohitkannada", "kannada"],
        "Taml": ["notosanstamil", "notosans-tamil", "lohittamil", "tamil"],
        "Telu": ["notosanstelugu", "notosans-telugu", "telugu"],
        "Mlym": ["notosansmalayalam", "notosans-malayalam", "malayalam"],
    }

    FONT_EXTS = {".ttf", ".otf", ".ttc"}

    def __init__(self, font_dirs: Iterable[str] | None = None) -> None:
        self.font_dirs: List[Path] = [Path(d) for d in (font_dirs or [])]

    def add_font_dir(self, d: str) -> None:
        p = Path(d)
        if p not in self.font_dirs:
            self.font_dirs.append(p)

    def _iter_font_files(self) -> Iterable[Path]:
        for d in self.font_dirs:
            if not d.exists() or not d.is_dir():
                continue
            for entry in sorted(d.iterdir()):
                if entry.suffix.lower() in self.FONT_EXTS and entry.is_file():
                    yield entry

    def _find_by_patterns(self, script: str) -> Path | None:
        candidates = list(self._iter_font_files())
        # search for preferred substrings
        prefs = self.PREFERRED.get(script, [])
        for pat in prefs:
            pat_l = pat.lower()
            for f in candidates:
                if pat_l in f.name.lower():
                    return f
        return None

    def font_for(self, language_or_script: str) -> str:
        """Return a font file path for the given language code or script key.

        Parameters:
          language_or_script: language code (e.g. 'hi', 'en') or script key ('Deva').

        Raises FontNotFoundError if no suitable font is found.
        """
        if not self.font_dirs:
            raise FontNotFoundError("No font directories configured; cannot select a font")

        # Normalize input: if language code, map to script
        script = self.LANG_TO_SCRIPT.get(language_or_script, language_or_script)

        # Try preferred patterns
        found = self._find_by_patterns(script)
        if found:
            return str(found)

        # Deterministic fallback: pick first available font file
        for f in self._iter_font_files():
            return str(f)

        raise FontNotFoundError(
            f"No suitable font found for '{language_or_script}' (script '{script}'). Searched {self.font_dirs}"
        )
