"""Conversation handlers for the music submission bot."""

import logging
import os
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes, ConversationHandler
from telegram.constants import ParseMode

from config import (
    OWNER_CHAT_ID,
    CHANNEL_ID,
    WAITING_FOR_MUSIC,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
    ALLOWED_AUDIO_MIME,
    ALLOWED_AUDIO_EXT,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _is_allowed_audio(document) -> bool:
    """Return True if the document looks like an allowed audio file."""
    if document is None:
        return False
    mime = (document.mime_type or "").lower()
    if mime in ALLOWED_AUDIO_MIME:
        return True
    name = (document.file_name or "").lower()
    return any(name.endswith(ext) for ext in ALLOWED_AUDIO_EXT)


def _submission_summary(data: dict) -> str:
    lines = [
        "🎵 <b>Нова заявка на музику</b>",
        "",
        f"🎼 <b>Назва:</b> {data.get('title', '—')}",
        f"🎤 <b>Виконавець:</b> {data.get('artist', '—')}",
    ]
    comment = data.get("comment")
    if comment:
        lines.append(f"💬 <b>Коментар:</b> {comment}")
    user = data.get("user")
    if user:
        name = user.full_name
        username = f" (@{user.username})" if user.username else ""
        lines.append(f"👤 <b>Від:</b> {name}{username} [<code>{user.id}</code>]")
    return "\n".join(lines)


def _approve_reject_keyboard(user_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("✅ Прийняти", callback_data=f"approve:{user_id}"),
            InlineKeyboardButton("❌ Відхилити", callback_data=f"reject:{user_id}"),
        ]
    ])


# ──────────────────────────────────────────────
# Conversation entry
# ──────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "👋 Ласкаво просимо до <b>Бота для подачі музики</b>!\n\n"
        "Ви можете надіслати музичний трек для розгляду на нашому каналі.\n\n"
        "Надішліть музичний файл (MP3, FLAC або WAV) "
        "або вставте посилання на музику (SoundCloud, YouTube, Spotify тощо).",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_MUSIC


# ──────────────────────────────────────────────
# Step 1 – Music file or link
# ──────────────────────────────────────────────

async def receive_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message

    # Audio attachment (Telegram audio or document)
    if message.audio:
        context.user_data["music_type"] = "audio"
        context.user_data["file_id"] = message.audio.file_id
        context.user_data["file_name"] = message.audio.file_name or "audio"
    elif message.document and _is_allowed_audio(message.document):
        context.user_data["music_type"] = "document"
        context.user_data["file_id"] = message.document.file_id
        context.user_data["file_name"] = message.document.file_name or "audio"
    elif message.text:
        # Accept any text as a link
        context.user_data["music_type"] = "link"
        context.user_data["link"] = message.text.strip()
    else:
        await message.reply_text(
            "⚠️ Будь ласка, надішліть файл MP3, FLAC або WAV, "
            "або вставте посилання на музику (наприклад, SoundCloud, YouTube, Spotify)."
        )
        return WAITING_FOR_MUSIC

    await message.reply_text(
        "🎼 Отримано! Тепер введіть <b>назву треку</b>.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_TITLE


# ──────────────────────────────────────────────
# Step 2 – Title
# ──────────────────────────────────────────────

async def receive_title(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    title = update.message.text.strip()
    if not title:
        await update.message.reply_text("Будь ласка, введіть коректну назву треку.")
        return WAITING_FOR_TITLE

    context.user_data["title"] = title
    await update.message.reply_text(
        "🎤 Чудово! Тепер введіть <b>ім'я виконавця</b>.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_ARTIST


# ──────────────────────────────────────────────
# Step 3 – Artist
# ──────────────────────────────────────────────

async def receive_artist(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    artist = update.message.text.strip()
    if not artist:
        await update.message.reply_text("Будь ласка, введіть коректне ім'я виконавця.")
        return WAITING_FOR_ARTIST

    context.user_data["artist"] = artist
    await update.message.reply_text(
        "💬 Бажаєте додати коментар? "
        "Напишіть його зараз або надішліть /skip, щоб пропустити."
    )
    return WAITING_FOR_COMMENT


# ──────────────────────────────────────────────
# Step 4 – Optional comment
# ──────────────────────────────────────────────

async def receive_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data["comment"] = update.message.text.strip()
    return await _forward_to_owner(update, context)


async def skip_comment(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("comment", None)
    return await _forward_to_owner(update, context)


# ──────────────────────────────────────────────
# Forward to owner
# ──────────────────────────────────────────────

async def _forward_to_owner(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    context.user_data["user"] = user

    data = context.user_data
    summary = _submission_summary(data)
    keyboard = _approve_reject_keyboard(user.id)

    music_type = data.get("music_type")

    try:
        if music_type == "audio":
            await context.bot.send_audio(
                chat_id=OWNER_CHAT_ID,
                audio=data["file_id"],
                caption=summary,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        elif music_type == "document":
            await context.bot.send_document(
                chat_id=OWNER_CHAT_ID,
                document=data["file_id"],
                caption=summary,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
        else:  # link
            await context.bot.send_message(
                chat_id=OWNER_CHAT_ID,
                text=f"{summary}\n\n🔗 <b>Посилання:</b> {data['link']}",
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
                disable_web_page_preview=False,
            )
    except Exception:
        logger.exception("Failed to forward submission to owner")
        await update.message.reply_text(
            "⚠️ Виникла помилка під час надсилання вашої заявки. Будь ласка, спробуйте пізніше."
        )
        return ConversationHandler.END

    await update.message.reply_text(
        "✅ Вашу заявку надіслано на розгляд!\n"
        "Ви отримаєте сповіщення, коли власник прийме рішення."
    )
    return ConversationHandler.END


# ──────────────────────────────────────────────
# Owner callback buttons
# ──────────────────────────────────────────────

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # Only the owner can use these buttons
    if query.from_user.id != OWNER_CHAT_ID:
        await query.answer("У вас немає прав для цієї дії.", show_alert=True)
        return

    action, submitter_id_str = query.data.split(":", 1)
    submitter_id = int(submitter_id_str)

    original = query.message

    if action == "approve":
        await _publish_to_channel(context, original)
        status_line = "✅ <b>Прийнято та опубліковано на каналі.</b>"
        user_msg = "🎉 Вашу заявку <b>схвалено</b> і опубліковано на каналі!"
    else:
        status_line = "❌ <b>Відхилено.</b>"
        user_msg = "😔 На жаль, ваша заявка <b>не була відібрана</b> цього разу. Дякуємо за участь!"

    # Edit owner message to remove buttons and show status
    new_text = (original.caption or original.text or "") + f"\n\n{status_line}"
    try:
        if original.caption is not None:
            await original.edit_caption(caption=new_text, parse_mode=ParseMode.HTML)
        else:
            await original.edit_text(text=new_text, parse_mode=ParseMode.HTML)
    except Exception:
        logger.warning("Could not edit owner message")

    # Notify submitter
    try:
        await context.bot.send_message(
            chat_id=submitter_id,
            text=user_msg,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        logger.warning("Could not notify submitter %s", submitter_id)


async def _publish_to_channel(context: ContextTypes.DEFAULT_TYPE, owner_msg) -> None:
    """Re-publish the approved submission to the channel."""
    caption = owner_msg.caption or owner_msg.text or ""
    # Strip the approve/reject keyboard caption additions if any
    clean_caption = caption.split("\n\n✅")[0].split("\n\n❌")[0]

    try:
        if owner_msg.audio:
            await context.bot.send_audio(
                chat_id=CHANNEL_ID,
                audio=owner_msg.audio.file_id,
                caption=clean_caption,
                parse_mode=ParseMode.HTML,
            )
        elif owner_msg.document:
            await context.bot.send_document(
                chat_id=CHANNEL_ID,
                document=owner_msg.document.file_id,
                caption=clean_caption,
                parse_mode=ParseMode.HTML,
            )
        else:
            await context.bot.send_message(
                chat_id=CHANNEL_ID,
                text=clean_caption,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=False,
            )
    except Exception:
        logger.exception("Failed to publish to channel")


# ──────────────────────────────────────────────
# Cancel
# ──────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "Заявку скасовано. Надішліть /start, коли захочете спробувати знову."
    )
    return ConversationHandler.END
