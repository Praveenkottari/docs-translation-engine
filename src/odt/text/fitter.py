from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from odt.document.models import BoundingBox, TextStyle
from odt.text.measure import measure_text


@dataclass
class FitResult:
    font_path: str
    font_size: float
    line_breaks: List[str]
    rendered_bbox: Tuple[float, float]
    fit_status: str  # 'fitted' or 'failed'
    line_spacing: float


class TextFitter:
    def __init__(self, min_font_size: float = 8.0, font_size_step: float = 1.0, min_line_spacing: float = -2.0):
        self.min_font_size = min_font_size
        self.font_size_step = font_size_step
        self.min_line_spacing = min_line_spacing

    def _wrap_text(self, text: str, font_path: str, font_size: float, max_width: float, line_spacing: float) -> Tuple[List[str], float]:
        """Return list of lines and total height for the wrapped text.

        Greedy word wrapping; if no spaces present, falls back to character wrap.
        """
        words = text.split(" ")
        # if entire text has no spaces, wrap by characters
        by_chars = len(words) == 1 and " " not in text

        lines: List[str] = []
        if by_chars:
            # break into characters
            current = ""
            for ch in text:
                attempt = current + ch
                m = measure_text(attempt, font_path, int(font_size), line_spacing=0)
                if m["width"] <= max_width or current == "":
                    current = attempt
                else:
                    lines.append(current)
                    current = ch
            if current:
                lines.append(current)
        else:
            current = ""
            for w in words:
                attempt = (current + " " + w).strip()
                m = measure_text(attempt, font_path, int(font_size), line_spacing=0)
                if m["width"] <= max_width or current == "":
                    current = attempt
                else:
                    lines.append(current)
                    current = w
            if current:
                lines.append(current)

        # compute total height
        if not lines:
            lines = [""]
        lm = measure_text(lines[0], font_path, int(font_size), line_spacing=0)
        line_h = lm["line_metrics"][0]["height"] if lm["line_metrics"] else 0
        total_h = 0.0
        for i, line in enumerate(lines):
            m = measure_text(line, font_path, int(font_size), line_spacing=0)
            h = m["line_metrics"][0]["height"] if m["line_metrics"] else line_h
            total_h += h
            if i < len(lines) - 1:
                total_h += line_spacing

        # width is max line width
        maxw = max(measure_text(l, font_path, int(font_size))["width"] for l in lines)
        return lines, float(maxw), float(total_h)

    def fit_text(self, text: str, bbox: BoundingBox, style: Optional[TextStyle], font_path: str, target_font_size: Optional[float] = None) -> FitResult:
        """Attempt to fit `text` into `bbox` using `font_path`.

        Strategy:
          1. Try original font size
          2. If too wide, try wrapping
          3. If still too tall, reduce font size stepwise until min_font_size
          4. Optionally reduce line spacing (down to min_line_spacing)
          5. Report failure if cannot fit
        """
        orig_size = target_font_size or (style.font_size if style and style.font_size else 12.0)
        size = float(orig_size)
        line_spacing = 0.0

        # Try decreasing font sizes
        font_size = size
        while font_size >= self.min_font_size:
            # First try single line
            m_all = measure_text(text, font_path, int(font_size), line_spacing=0)
            if m_all["width"] <= bbox.width and m_all["height"] <= bbox.height:
                return FitResult(font_path=font_path, font_size=font_size, line_breaks=[text], rendered_bbox=(m_all["width"], m_all["height"]), fit_status="fitted", line_spacing=0.0)

            # Try wrapping with current font size and varying line spacing
            ls = 0.0
            while ls >= self.min_line_spacing:
                lines, w, h = self._wrap_text(text, font_path, font_size, bbox.width, ls)
                if w <= bbox.width and h <= bbox.height:
                    return FitResult(font_path=font_path, font_size=font_size, line_breaks=lines, rendered_bbox=(w, h), fit_status="fitted", line_spacing=ls)
                ls -= 1.0

            font_size -= self.font_size_step

        # If we reach here, fitting failed
        # Return best-effort with smallest font size attempted
        final_lines, final_w, final_h = self._wrap_text(text, font_path, max(self.min_font_size, 1.0), bbox.width, self.min_line_spacing)
        return FitResult(font_path=font_path, font_size=max(self.min_font_size, 1.0), line_breaks=final_lines, rendered_bbox=(final_w, final_h), fit_status="failed", line_spacing=self.min_line_spacing)
