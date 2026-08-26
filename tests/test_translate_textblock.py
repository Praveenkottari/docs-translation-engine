from __future__ import annotations

from odt.document.models import BoundingBox, TextBlock
from odt.lang.detector import SimpleScriptLanguageDetector
from odt.translation.backend import MockTranslationBackend
from odt.translation.processor import translate_textblock, translate_blocks


def make_block(id: str, text: str) -> TextBlock:
    return TextBlock(id=id, bbox=BoundingBox(0, 0, 10, 2), text=text)


def test_translate_english_to_hindi():
    block = make_block("b1", "This is a test.")
    detector = SimpleScriptLanguageDetector()
    backend = MockTranslationBackend()
    backend.initialize()
    out = translate_textblock(block, backend, "hi", detector)
    assert out.id == block.id
    assert out.bbox == block.bbox
    assert out.language.code == "hi"
    assert out.text.startswith("[en->hi]")


def test_translate_english_to_kannada():
    block = make_block("b2", "Measurement 10 MPa and value 3.5")
    detector = SimpleScriptLanguageDetector()
    backend = MockTranslationBackend()
    backend.initialize()
    out = translate_textblock(block, backend, "kn", detector)
    assert out.id == block.id
    assert out.bbox == block.bbox
    assert out.language.code == "kn"
    # ensure numbers/units survive
    assert "10 MPa" in out.text
    assert out.text.startswith("[en->kn]")


def test_mixed_language_blocks():
    # Latin + Devanagari mix
    mixed_text = "Test English और कुछ हिंदी शब्द"
    block = make_block("b3", mixed_text)
    detector = SimpleScriptLanguageDetector()
    backend = MockTranslationBackend()
    backend.initialize()
    out = translate_textblock(block, backend, "en", detector, skip_if_target_language=False)
    assert out.id == block.id
    assert out.bbox == block.bbox
    assert out.language.code == "en"
    # tokens preserved (none here) and text translated marker present
    assert out.text.startswith("[und->en]") or out.text.startswith("[hi->en]") or out.text.startswith("[en->en]")


def test_numbers_units_engineering_ids_preserved():
    text = "Design Pressure: 10 MPa, Tag: PV-1024, Spec SA-516 Gr.70"
    block = make_block("b4", text)
    detector = SimpleScriptLanguageDetector()
    backend = MockTranslationBackend()
    backend.initialize()
    out = translate_textblock(block, backend, "ta", detector)
    assert out.id == block.id
    assert out.bbox == block.bbox
    # numbers/units/tags should remain present after translation+restore
    assert "10 MPa" in out.text
    assert "PV-1024" in out.text
    assert "SA-516" in out.text


def test_translate_blocks_batch():
    blocks = [make_block("b5", "One"), make_block("b6", "Two")]
    backend = MockTranslationBackend()
    backend.initialize()
    detector = SimpleScriptLanguageDetector()
    outs = translate_blocks(blocks, backend, "hi", detector)
    assert len(outs) == 2
    assert outs[0].id == "b5" and outs[1].id == "b6"
