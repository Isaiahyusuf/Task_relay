"""
Machine translation utility using deep-translator (Google Translate free tier).

Usage:
    from src.bot.utils.translate import translate_text

    translated = await translate_text("Hello", target_lang="ps")
    # → "سلام"
"""

import asyncio
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_LANG_MAP: dict[str, str] = {
    "en": "en",
    "ps": "ps",
    "my": "my",
}


async def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str:
    """
    Translate *text* into *target_lang*.

    - Returns the original text unchanged if:
      - target_lang is the same as source_lang
      - target_lang is "en" and source_lang is "en" (or auto with English input)
      - The translation API fails for any reason
    - Runs the synchronous GoogleTranslator in a thread pool to stay async-safe.
    """
    if not text or not text.strip():
        return text

    target = _LANG_MAP.get(target_lang, "en")
    source = _LANG_MAP.get(source_lang, "auto") if source_lang != "auto" else "auto"

    if source != "auto" and source == target:
        return text

    try:
        from deep_translator import GoogleTranslator

        def _translate() -> str:
            translator = GoogleTranslator(source=source, target=target)
            result = translator.translate(text)
            return result if result else text

        translated = await asyncio.to_thread(_translate)
        return translated
    except Exception as exc:
        logger.warning("translate_text failed (target=%s): %s", target_lang, exc)
        return text
