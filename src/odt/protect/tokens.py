from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass
class TokenMap:
    mapping: Dict[str, str]

    def __init__(self) -> None:
        self.mapping = {}

    def add(self, token: str, original: str) -> None:
        self.mapping[token] = original

    def restore(self, text: str) -> str:
        # Replace tokens with original values. Use longest-first to avoid substring issues.
        for token in sorted(self.mapping.keys(), key=len, reverse=True):
            text = text.replace(token, self.mapping[token])
        return text


class Protector:
    TOKEN_FMT = "__ODT_TOKEN_{:04d}__"

    def __init__(self) -> None:
        self._counter = 0

        # Patterns list: ordered to prefer longest/most specific first
        self._patterns: List[Tuple[str, re.Pattern]] = [
            ("url", re.compile(r"https?://[\w\-\.\/~:?#@!$&'()*+,;=%]+", re.IGNORECASE)),
            ("email", re.compile(r"\b[\w.\-+%]+@[\w.\-]+\.[A-Za-z]{2,}\b")),
            # UNC path (\\server\share\file)
            ("unc_path", re.compile(r"\\\\[^\s,;:()]+(?:\\\\[^\s,;:()]+)+")),
            ("windows_path", re.compile(r"[A-Za-z]:\\(?:[^\\\s]+\\)*[^\\\s]+")),
            ("unix_path", re.compile(r"(/[^\s,;:()]+)+")),
            # engineering tags like PV-1024, TAG-1234
            ("eng_tag", re.compile(r"\b[A-Z]{1,5}-\d{1,6}\b")),
            # SA-516 Gr.70 or similar with grade
            ("grade", re.compile(r"\b[A-Z]{1,5}-\d{1,6}\s+Gr\.\s?\d{1,3}\b", re.IGNORECASE)),
            # chemical formulas requiring at least one digit (e.g., C6H12O6)
            ("chem", re.compile(r"\b(?:[A-Z][a-z]?\d+){1,}\b")),
            # numbers with units (including °C, °F)
            (
                "number_unit",
                re.compile(r"\b-?\d{1,3}(?:[\,\.]\d+)?\s?(?:°[CF]|MPa|kPa|Pa|bar|mmHg|mm|cm|m|km|kg|g|mg|L|ml|W|kW|V|mV|A|mA|Hz|kHz|MHz|ppm)\b", re.IGNORECASE),
            ),
            # percentages
            ("percent", re.compile(r"\b-?\d+(?:[\.,]\d+)?\s?%\b")),
            # ranges like 10-20 or 10–20
            ("range", re.compile(r"\b-?\d+(?:[\.,]\d+)?\s?[\-–]\s?-?\d+(?:[\.,]\d+)?\b")),
            # dates YYYY-MM-DD, DD/MM/YYYY, DD.MM.YYYY
            ("date_iso", re.compile(r"\b\d{4}-\d{2}-\d{2}\b")),
            ("date_slash", re.compile(r"\b\d{1,2}/\d{1,2}/\d{2,4}\b")),
            ("date_dot", re.compile(r"\b\d{1,2}\.\d{1,2}\.\d{2,4}\b")),
            # time H:MM or HH:MM:SS
            ("time", re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b")),
            # decimal or integer (negative allowed)
            ("number", re.compile(r"\b-?\d{1,3}(?:[\,\.]\d+)?\b")),
        ]

    def _next_token(self) -> str:
        self._counter += 1
        return self.TOKEN_FMT.format(self._counter)

    def protect(self, text: str) -> Tuple[str, TokenMap]:
        token_map = TokenMap()

        if not text:
            return text, token_map

        out = []
        idx = 0
        length = len(text)

        while idx < length:
            # find earliest match among patterns starting at idx or after
            earliest = None  # tuple(start, end, match_text)
            earliest_pat = None

            for name, pat in self._patterns:
                m = pat.search(text, idx)
                if m:
                    s, e = m.start(), m.end()
                    if earliest is None or s < earliest[0]:
                        earliest = (s, e, m.group(0))
                        earliest_pat = name

            if earliest is None:
                out.append(text[idx:])
                break

            s, e, match_text = earliest
            if s > idx:
                out.append(text[idx:s])

            token = self._next_token()
            out.append(token)
            token_map.add(token, match_text)

            idx = e

        protected = "".join(out)
        return protected, token_map


def protect(text: str) -> Tuple[str, TokenMap]:
    p = Protector()
    return p.protect(text)


def restore(text: str, token_map: TokenMap) -> str:
    return token_map.restore(text)
