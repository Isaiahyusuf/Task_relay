from aiogram import Router, F
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from sqlalchemy import select
from src.bot.database import async_session, User
from src.bot.i18n import LANGUAGES, variants, msg
from src.bot.utils.keyboards import get_main_menu_keyboard
import logging

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.in_(variants("Language")))
async def btn_language(message: Message):
    if not async_session:
        await message.answer("Database not available.")
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == message.from_user.id)
        )
        user = result.scalar_one_or_none()

    if not user:
        await message.answer("Please register first with /start")
        return

    lang = getattr(user, "language", "en") or "en"

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=("✅ " if lang == "en" else "") + LANGUAGES["en"],
            callback_data="set_lang:en"
        )],
        [InlineKeyboardButton(
            text=("✅ " if lang == "ps" else "") + LANGUAGES["ps"],
            callback_data="set_lang:ps"
        )],
        [InlineKeyboardButton(
            text=("✅ " if lang == "my" else "") + LANGUAGES["my"],
            callback_data="set_lang:my"
        )],
    ])

    await message.answer(
        msg("language_prompt", lang),
        reply_markup=keyboard,
        parse_mode="Markdown"
    )


@router.callback_query(F.data.startswith("set_lang:"))
async def set_language_callback(callback: CallbackQuery):
    lang_code = callback.data.split(":")[1]

    if lang_code not in LANGUAGES:
        await callback.answer("Invalid language", show_alert=True)
        return

    if not async_session:
        await callback.answer("Database error", show_alert=True)
        return

    async with async_session() as session:
        result = await session.execute(
            select(User).where(User.telegram_id == callback.from_user.id)
        )
        user = result.scalar_one_or_none()

        if not user:
            await callback.answer("User not found", show_alert=True)
            return

        user.language = lang_code
        await session.commit()
        role = user.role

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=("✅ " if lang_code == "en" else "") + LANGUAGES["en"],
            callback_data="set_lang:en"
        )],
        [InlineKeyboardButton(
            text=("✅ " if lang_code == "ps" else "") + LANGUAGES["ps"],
            callback_data="set_lang:ps"
        )],
        [InlineKeyboardButton(
            text=("✅ " if lang_code == "my" else "") + LANGUAGES["my"],
            callback_data="set_lang:my"
        )],
    ])

    lang_set_key = f"language_set_{lang_code}"
    confirm = msg(lang_set_key, lang_code)

    await callback.message.edit_reply_markup(reply_markup=keyboard)

    new_menu = get_main_menu_keyboard(role, lang=lang_code)
    await callback.message.answer(confirm, reply_markup=new_menu)
    await callback.answer()
