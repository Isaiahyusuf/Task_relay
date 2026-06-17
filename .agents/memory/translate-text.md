---
name: translate_text utility
description: How the async translate_text wrapper works and when to use it vs static i18n entries.
---

## Location
`src/bot/utils/translate.py`

## Behavior
- Wraps `deep_translator.GoogleTranslator`
- Returns original text on any exception (never crashes)
- LRU cache: 256 entries (key = text + target_lang + source_lang)
- Chunks input > 5000 chars automatically
- Broadcast loop caches per-language to avoid redundant API calls

## When to use
- **Static i18n entries** (`MESSAGES` in `src/bot/i18n.py`): short, frequently used strings (confirmations, prompts, notifications). Defined once with en/ps/my variants.
- **translate_text dynamically**: long one-off texts that change rarely (help text, about text). Called at request time with `if lang != "en"` guard to avoid unnecessary API calls.

## Signature
```python
async def translate_text(text: str, target_lang: str, source_lang: str = "auto") -> str
```
Language codes: `"en"`, `"ps"` (Pashto), `"my"` (Burmese).
