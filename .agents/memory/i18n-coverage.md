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
- FSM flows: store `lang` in state data at flow entry (`await state.update_data(lang=lang)`), then retrieve with `data.get("lang") or await get_recipient_lang(...)` in subsequent steps.

## Completed files

### scheduler.py
- `check_reminders` → `i18n_msg("pending_job_reminder", ...)` to sub
- `check_auto_close` → `i18n_msg("job_auto_cancelled", ...)` to supervisor

### auth.py
- welcome_back, delete account flow, show_help (translate_text), btn_about

### subcontractor.py — fully i18n'd

### supervisor.py — fully i18n'd

### admin.py — fully i18n'd (completed in latest session)
- All code creation FSM steps (process_code_input, process_role_selection, create_code_with_team, finalize_code_creation, cancel handlers)
- Switch role flow (btn_switch_role_super_admin, handle_super_admin_switch, handle_switch_team_selection, btn_return_to_super_admin)
- User management (show_user_list, show_users_by_role, handle_manage_user, handle_delete_user_request, handle_confirm_delete, back_to_users)
- Messaging flow (btn_send_message, process_message_target, proceed_to_compose, send_broadcast_message, cancel_message)
- Availability flow (btn_request_availability, toggle_availability_request_selection, cancel_availability_request, send_availability_request)
- Weekly availability view (btn_weekly_availability)
- All db_unavailable, user_not_found_err, not_authorized, cannot_return_gm strings

## i18n keys added in latest session (admin.py round)
~50 keys added to MESSAGES in i18n.py covering code creation, switch role,
user management, messaging, availability. See i18n.py starting around line 1232.

## Known minor gaps (acceptable)
- Supervisor job creation step body prompts (step 2–7 form questions) — English only
- safety_checklist.py — English only (super_admin/admin-only feature)
- Custom roles / regions / teams management pages in admin.py — English only (super_admin only, not multilingual users)
