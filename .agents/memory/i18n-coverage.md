---
name: i18n coverage audit
description: Which files/handlers had missing language logic and how they were fixed.
---

## Rule
Every message sent to a user — whether background (scheduler) or interactive (handler) — must use `i18n_msg(key, lang=lang)` with the recipient's language fetched via `get_recipient_lang(telegram_id)`.

**Why:** The bot has Pashto (ps) and Burmese (my) speaking subcontractors who see English if i18n is skipped.

**How to apply:**
- Background alerts (scheduler, broadcast): always `get_recipient_lang` on the recipient's telegram_id.
- Interactive handler responses: use `get_recipient_lang(message.from_user.id)` or read `user.language` if the user object is already loaded.
- Long static texts (help, about): use `translate_text(text, target_lang=lang)` dynamically rather than hardcoding Pashto/Burmese in MESSAGES.

## Fixed in latest session

### scheduler.py
- `check_reminders` → `i18n_msg("pending_job_reminder", ...)` to sub
- `check_auto_close` → `i18n_msg("job_auto_cancelled", ...)` to supervisor

### auth.py
- welcome_back already existed in MESSAGES — wired it up (was hardcoded f-string)
- delete account flow: `account_delete_confirm`, `account_deleted`, `account_delete_cancelled`
- `show_help`: added `translate_text` at the end if `lang != "en"`
- `btn_about`: added DB lang lookup + `translate_text` if needed

### subcontractor.py
- `job_accepted_confirm`, `job_marked_done_confirm`, `job_started_confirm`, `job_completed_confirm`
- `no_jobs_in_progress`, `select_job_to_submit`
- `submission_notes_prompt`, `submission_photos_prompt`, `submission_cancelled`
- `photo_required_prompt`, `photo_added_sub`
- `quote_notes_prompt`, `quote_submitted_confirm`, `quote_cancelled`

### supervisor.py
- All 7 occurrences of "Job creation cancelled." → `i18n_msg("job_creation_cancelled", lang=lang)`
- `job_saved_draft` → `i18n_msg("job_saved_draft", ...)`

## Remaining gaps (not yet fixed)
- `admin.py` line 1519: admin deleting another user's account — hardcoded English (low priority, admin is typically English-speaking)
- Various minor error strings ("Session expired", "Database not available", etc.) — not translated
- Supervisor job creation flow prompts (step 2–7 text content) — only the cancel/save messages were i18n'd; the step body prompts still in English
