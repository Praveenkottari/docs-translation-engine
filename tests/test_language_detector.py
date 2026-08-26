from __future__ import annotations

from odt.lang.detector import SimpleScriptLanguageDetector
from odt.document.models import LanguageInfo


def test_detect_english():
    det = SimpleScriptLanguageDetector()
    text = "This is a test sentence to detect English language. " * 3
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "en"
    assert info.confidence > 0.8


def test_detect_hindi():
    det = SimpleScriptLanguageDetector()
    text = "यह एक परीक्षण वाक्य है। " * 4
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "hi"
    assert info.script == "Deva"
    assert info.confidence > 0.8


def test_detect_kannada():
    det = SimpleScriptLanguageDetector()
    text = "ಇದು ಒಂದು ಪರೀಕ್ಷೆ ವಾಕ್ಯವಾಗಿದೆ" * 3
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "kn"
    assert info.script == "Knda"


def test_detect_tamil():
    det = SimpleScriptLanguageDetector()
    text = "இது ஒரு சோதனை வாக்கியம்" * 3
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "ta"
    assert info.script == "Taml"


def test_detect_telugu():
    det = SimpleScriptLanguageDetector()
    text = "ఇది ఒక పరీక్షను వాక్యం" * 3
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "te"
    assert info.script == "Telu"


def test_detect_malayalam():
    det = SimpleScriptLanguageDetector()
    text = "ഇത് ഒരു പരീക്ഷാസന്ദേശം" * 3
    info = det.detect(text)
    assert isinstance(info, LanguageInfo)
    assert info.code == "ml"
    assert info.script == "Mlym"
