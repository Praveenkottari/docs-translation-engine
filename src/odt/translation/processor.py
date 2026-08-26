from __future__ import annotations

from typing import Iterable, List, Optional

from odt.document.models import LanguageInfo, TextBlock
from odt.lang.detector import LanguageDetector
from odt.protect.tokens import protect, restore, TokenMap
from odt.translation.backend import TranslationBackend


def translate_textblock(
    block: TextBlock,
    backend: TranslationBackend,
    target_language: str,
    language_detector: Optional[LanguageDetector] = None,
    skip_if_target_language: bool = True,
    source_language: Optional[str] = None,
) -> TextBlock:
    """Translate a single TextBlock following the pipeline:
    language detection -> protect tokens -> translate -> restore tokens.

    Preserves `id` and `bbox`. Returns a new `TextBlock` with translated text and
    `language` set to the detected/target language.
    """
    # detect source language if not provided
    detected: LanguageInfo
    if source_language:
        detected = LanguageInfo(code=source_language, name=source_language)
    else:
        if language_detector is not None:
            detected = language_detector.detect(block.text)
        else:
            # fallback to unknown
            detected = LanguageInfo(code="und", name="und", confidence=0.0)

    # Optionally skip if already in target language
    if skip_if_target_language and detected.code == target_language:
        return block

    # Protect tokens
    protected_text, token_map = protect(block.text)

    # Ensure backend initialized is the caller responsibility; call translate
    translated_protected = backend.translate(protected_text, detected.code, target_language)

    # Restore tokens
    translated = restore(translated_protected, token_map)

    # Build new TextBlock with same id and bbox, preserve style/confidence/source
    new_lang = LanguageInfo(code=target_language, name=target_language, confidence=1.0)

    return TextBlock(
        id=block.id,
        bbox=block.bbox,
        text=translated,
        language=new_lang,
        confidence=block.confidence,
        style=block.style,
        source=block.source,
    )


def translate_blocks(
    blocks: Iterable[TextBlock],
    backend: TranslationBackend,
    target_language: str,
    language_detector: Optional[LanguageDetector] = None,
    skip_if_target_language: bool = True,
) -> List[TextBlock]:
    return [
        translate_textblock(b, backend, target_language, language_detector, skip_if_target_language)
        for b in blocks
    ]


def translate_blocks_batched(
    blocks: Iterable[TextBlock],
    backend: TranslationBackend,
    target_language: str,
    language_detector: Optional[LanguageDetector] = None,
    skip_if_target_language: bool = True,
) -> List[TextBlock]:
    """Translate blocks by batching compatible blocks.

    Groups blocks by (source_language, target_language) where source_language is
    detected per-block (or taken from `block.language` if present and not 'und').

    Ensures original ordering and IDs are preserved.
    """
    # Prepare lists in input order
    blocks_list = list(blocks)
    n = len(blocks_list)

    # Per-block metadata
    detected_codes: List[str] = ["und"] * n
    to_translate_flags: List[bool] = [False] * n
    protected_texts: List[Optional[str]] = [None] * n
    token_maps: List[Optional[TokenMap]] = [None] * n

    # First pass: detect languages and prepare protected texts
    for i, b in enumerate(blocks_list):
        # detect source language
        if b.language is not None and b.language.code and b.language.code != "und":
            src = b.language.code
        elif language_detector is not None:
            src = language_detector.detect(b.text).code
        else:
            src = "und"
        detected_codes[i] = src

        if skip_if_target_language and src == target_language:
            to_translate_flags[i] = False
            continue

        # protect tokens for each block individually
        prot, tmap = protect(b.text)
        protected_texts[i] = prot
        token_maps[i] = tmap
        to_translate_flags[i] = True

    # Group indices by (src, target)
    groups: dict[tuple[str, str], list[int]] = {}
    for i, should in enumerate(to_translate_flags):
        if not should:
            continue
        key = (detected_codes[i], target_language)
        groups.setdefault(key, []).append(i)

    # For each group, build batch, call backend.translate_batch, then restore
    translated_results: List[Optional[str]] = [None] * n
    for (src, tgt), indices in groups.items():
        batch_texts = [protected_texts[i] or "" for i in indices]
        # call backend batch
        batch_translated = backend.translate_batch(batch_texts, src, tgt)
        # restore per item
        for idx_in_group, i in enumerate(indices):
            restored = restore(batch_translated[idx_in_group], token_maps[i])
            translated_results[i] = restored

    # Build output list preserving order and original ids/bboxes
    output: List[TextBlock] = []
    for i, b in enumerate(blocks_list):
        if not to_translate_flags[i]:
            # unchanged block (possibly skipped)
            output.append(b)
            continue
        assert translated_results[i] is not None
        new_lang = LanguageInfo(code=target_language, name=target_language, confidence=1.0)
        output.append(
            TextBlock(
                id=b.id,
                bbox=b.bbox,
                text=translated_results[i],
                language=new_lang,
                confidence=b.confidence,
                style=b.style,
                source=b.source,
            )
        )

    return output
