from __future__ import annotations

from typing import Dict, List, Tuple

from PIL import Image, ImageDraw, ImageFont


def _load_font(font_path: str | None, size: int) -> ImageFont.FreeTypeFont:
    if font_path:
        return ImageFont.truetype(font_path, size)
    # fallback to default PIL font
    return ImageFont.load_default()


def measure_text(
    text: str,
    font_path: str | None,
    font_size: int = 12,
    line_spacing: int = 0,
) -> Dict[str, object]:
    """Measure text dimensions.

    Returns:
      {
        'width': float,
        'height': float,
        'line_metrics': [ {'text':line,'width':w,'ascent':a,'descent':d,'height':h}, ... ]
      }

    Uses Pillow's FreeTypeFont and ImageDraw.textbbox to compute accurate bounds.
    """
    if text is None:
        text = ""

    font = _load_font(font_path, font_size)

    # Create a temporary image to use ImageDraw
    img = Image.new("RGB", (2048, 2048), color=(255, 255, 255))
    draw = ImageDraw.Draw(img)

    # metrics from font
    try:
        ascent, descent = font.getmetrics()
    except Exception:
        ascent, descent = 0, 0

    lines = text.splitlines() or [""]
    line_metrics: List[Dict[str, object]] = []
    maxw = 0
    total_h = 0

    for idx, line in enumerate(lines):
        if line == "":
            # measure empty line by ascent+descent
            w = 0
            h = ascent + descent
        else:
            # use textbbox for more accurate measurement
            try:
                bbox = draw.textbbox((0, 0), line, font=font)
                w = bbox[2] - bbox[0]
                h = bbox[3] - bbox[1]
            except Exception:
                w, h = draw.textsize(line, font=font)

        maxw = max(maxw, w)
        # line height: use ascent+descent for consistent line spacing
        line_h = ascent + descent
        # if textbbox returned larger height, use it
        if h > line_h:
            line_h = h

        # apply line spacing except after last line
        total_h += line_h
        if idx < len(lines) - 1:
            total_h += line_spacing

        line_metrics.append({
            "text": line,
            "width": float(w),
            "ascent": float(ascent),
            "descent": float(descent),
            "height": float(line_h),
        })

    return {"width": float(maxw), "height": float(total_h), "line_metrics": line_metrics}
