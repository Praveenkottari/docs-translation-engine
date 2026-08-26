from __future__ import annotations

import pytest

from odt.translation.backend import MockTranslationBackend, TranslationError


def test_mock_initialize_required():
    mock = MockTranslationBackend()
    with pytest.raises(RuntimeError):
        mock.translate("hello", "en", "hi")
    mock.initialize()
    assert mock.translate("hello", "en", "hi") == "[en->hi] hello"


def test_mock_batch_and_single_consistency():
    mock = MockTranslationBackend()
    mock.initialize()
    texts = ["one", "two", "three"]
    single = [mock.translate(t, "en", "fr") for t in texts]
    batch = mock.translate_batch(texts, "en", "fr")
    assert single == batch


def test_mock_supported_pairs():
    pairs = [("en", "fr"), ("hi", "en")]
    mock = MockTranslationBackend(supported_pairs=pairs)
    mock.initialize()
    assert mock.translate("a", "en", "fr") == "[en->fr] a"
    assert mock.translate("b", "hi", "en") == "[hi->en] b"
    with pytest.raises(TranslationError):
        mock.translate("x", "en", "de")


def test_mock_translate_batch_unsupported_pair():
    mock = MockTranslationBackend(supported_pairs=[("en", "fr")])
    mock.initialize()
    with pytest.raises(TranslationError):
        mock.translate_batch(["a", "b"], "en", "de")
