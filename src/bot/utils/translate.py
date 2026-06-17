"""
Machine translation utility using deep-translator (Google Translate free tier).

Usage:
    from src.bot.utils.translate import translate_text

    translated = await translate_text("Hello", target_lang="ps")
    # → "سلام"
"""

import asyncio
import logging

logger = logging.getLogger(__name__)

_LANG_MAP: dict[str, str] = {
    "en": "en",
    "ps": "ps",
    "my": "my",
}

_CHUNK_SIZE = 4900


def _sync_translate(text: str, source: str, target: str) -> str:
    """Synchronous translation with chunking for texts over 4900 chars."""
    from deep_translator import GoogleTranslator

    if len(text) <= _CHUNK_SIZE:
        translator = GoogleTranslator(source=source, target=target)
        result = translator.translate(text)
        return result if result else text

    # Split into chunks at sentence or word boundaries
    chunks: list[str] = []
    remaining = text
    while remaining:
        if len(remaining) <= _CHUNK_SIZE:
            chunks.append(remaining)
            break
        split_at = remaining.rfind(" ", 0, _CHUNK_SIZE)
        if split_at == -1:
            split_at = _CHUNK_SIZE
        chunks.append(remaining[:split_at])
        remaining = remaining[split_at:].lstrip()

    translator = GoogleTranslator(source=source, target=target)
    translated_chunks = [translator.translate(c) or c for c in chunks]
    return " ".join(translated_chunks)


# Simple in-process cache: (text, source, target) → translated string
_cache: dict[tuple[str, str, str], str] = {}
_CACHE_MAX = 256


async def translate_text(text: str | None, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate *text* into *target_lang*.

    - Returns the original text unchanged (never None) if:
      - text is None, empty, or whitespace-only
      - target_lang is the same as source_lang (skips API call)
      - The translation API fails for any reason (silent fallback)
    - Caches results in memory so repeated identical calls (e.g. in broadcast
      loops) hit zero API calls after the first.
    - Chunks text longer than 4900 chars to stay within Google's 5000-char limit.
    """
    if not text or not text.strip():
        return text or ""

    target = _LANG_MAP.get(target_lang, "en")
    source = _LANG_MAP.get(source_lang, "auto") if source_lang != "auto" else "auto"

    if source != "auto" and source == target:
        return text

    cache_key = (text, source, target)
    if cache_key in _cache:
        return _cache[cache_key]

    try:
        translated = await asyncio.to_thread(_sync_translate, text, source, target)

        # Evict oldest entry if cache is full
        if len(_cache) >= _CACHE_MAX:
            oldest = next(iter(_cache))
            del _cache[oldest]
        _cache[cache_key] = translated
        return translated
    except Exception as exc:
        logger.warning("translate_text failed (target=%s): %s", target_lang, exc)
        return text
