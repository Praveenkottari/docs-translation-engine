from __future__ import annotations

from typing import List, Sequence

from odt.document.models import BoundingBox, TextBlock
from odt.lang.detector import SimpleScriptLanguageDetector
from odt.translation.backend import MockTranslationBackend
from odt.translation.processor import translate_blocks_batched


def make_block(id: str, text: str) -> TextBlock:
    return TextBlock(id=id, bbox=BoundingBox(0, 0, 10, 2), text=text)


def test_batched_preserves_ids_and_order():
    blocks = [make_block(f"b{i}", t) for i, t in enumerate(["One", "Two", "Three"], start=1)]
    backend = MockTranslationBackend()
    backend.initialize()
    detector = SimpleScriptLanguageDetector()
    outs = translate_blocks_batched(blocks, backend, "hi", detector)
    assert [b.id for b in outs] == ["b1", "b2", "b3"]
    assert [b.text for b in outs] == ["[en->hi] One", "[en->hi] Two", "[en->hi] Three"]


def test_mixed_language_page_batching():
    # English, Hindi, English
    blocks = [
        make_block("b1", "Hello world"),
        make_block("b2", "यह एक परीक्षण है"),
        make_block("b3", "Another English sentence"),
    ]
    backend = MockTranslationBackend()
    backend.initialize()
    detector = SimpleScriptLanguageDetector()
    # Translate all to English (so Hindi block should be translated)
    outs = translate_blocks_batched(blocks, backend, "en", detector)

    # b1 and b3 were English and may be skipped (if skip_if_target_language True)
    # Default skips blocks already in target language, so b1 and b3 should be unchanged
    assert outs[0].id == "b1" and outs[0].text == "Hello world"
    assert outs[2].id == "b3" and outs[2].text == "Another English sentence"

    # b2 should be translated from Hindi to English
    assert outs[1].id == "b2"
    assert outs[1].text.startswith("[hi->en]")


def test_batching_does_not_change_output_mapping_and_uses_batch_api():
    # Spy backend that records batch calls
    class SpyBackend(MockTranslationBackend):
        def __init__(self):
            super().__init__()
            self.calls: List[tuple[str, str, Sequence[str]]] = []

        def translate_batch(self, texts: Sequence[str], source_language: str, target_language: str) -> List[str]:
            self.calls.append((source_language, target_language, texts))
            return super().translate_batch(texts, source_language, target_language)

    blocks = [
        make_block("b1", "One"),
        make_block("b2", "दो"),  # Hindi
        make_block("b3", "Three"),
    ]
    backend = SpyBackend()
    backend.initialize()
    detector = SimpleScriptLanguageDetector()
    outs = translate_blocks_batched(blocks, backend, "en", detector)

    # ensure mapping preserved
    assert [b.id for b in outs] == ["b1", "b2", "b3"]

    # verify that translate_batch was called at least once (for Hindi->en)
    assert any(call[0] == "hi" and call[1] == "en" for call in backend.calls)
