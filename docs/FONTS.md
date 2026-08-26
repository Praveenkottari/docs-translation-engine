Fonts and Licensing
====================

This project requires fonts capable of rendering target languages/scripts. Fonts are not bundled by this project; you must provide them from trusted sources and ensure you comply with their licenses.

Recommendations
---------------
- Google Noto family (wide script coverage) is a common choice. Verify the license for the specific Noto fonts you use.
- DejaVu fonts and Liberation fonts provide good Latin coverage.

How to install
---------------
Place font files (TTF/OTF/TTC) in a directory and provide that directory to `FontManager` construction, for example:

```py
from odt.font.manager import FontManager
fm = FontManager(font_dirs=["/usr/share/fonts/truetype", "/home/me/.local/share/fonts"])
path = fm.font_for("hi")
```

Licensing notes
---------------
- Always record the exact font package name and version and the license (SPDX) in `THIRD_PARTY_LICENSES.md` for auditing.
- Some fonts require attribution or have restrictions; check the font project's license before redistributing.
