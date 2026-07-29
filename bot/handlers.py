"""Conversation handlers for the music submission bot."""

import logging
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
    WAITING_FOR_IMAGE,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
    ALLOWED_AUDIO_MIME,
    ALLOWED_AUDIO_EXT,
)

from database import (
    add_submission,
    get_submission,
    approve_submission,
    reject_submission,
    get_pending,
    get_stats,
)

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────

def _is_allowed_audio(document) -> bool:
    if document is None:
        return False
    mime = (document.mime_type or "").lower()
    if mime in ALLOWED_AUDIO_MIME:
        return True
    name = (document.file_name or "").lower()
    return any(name.endswith(ext) for ext in ALLOWED_AUDIO_EXT)


def _submission_caption(data: dict) -> str:
    """Build the caption shown to the owner and published to the channel."""
    lines = ["🎵 <b>Нова заявка на музику</b>", ""]
    lines.append(f"🎵 <b>Трек:</b> {data.get('title', '—')}")
    lines.append(f"👤 <b>Виконавець:</b> {data.get('artist', '—')}")
    comment = data.get("comment")
    if comment:
        lines.append(f"💬 <b>Коментар:</b> {comment}")
    link = data.get("link")
    if link:
        lines.append(f"🔗 <b>Посилання:</b> {link}")
    user = data.get("user")
    if user:
        name = user.full_name
        username = f" (@{user.username})" if user.username else ""
        lines.append(f"👤 <b>Від:</b> {name}{username} [<code>{user.id}</code>]")
    return "\n".join(lines)


def _channel_caption(data: dict) -> str:
    """Shorter caption for the public channel post (no sender info)."""
    lines = []
    lines.append(f"🎵 <b>{data.get('title', '—')}</b>")
    lines.append(f"👤 {data.get('artist', '—')}")
    comment = data.get("comment")
    if comment:
        lines.append(f"💬 {comment}")
    link = data.get("link")
    if link:
        lines.append(f"🔗 {link}")
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

    if message.audio:
        context.user_data["music_type"] = "audio"
        context.user_data["file_id"] = message.audio.file_id
        context.user_data["file_name"] = message.audio.file_name or "audio"
    elif message.document and _is_allowed_audio(message.document):
        context.user_data["music_type"] = "document"
        context.user_data["file_id"] = message.document.file_id
        context.user_data["file_name"] = message.document.file_name or "audio"
    elif message.text:
        context.user_data["music_type"] = "link"
        context.user_data["link"] = message.text.strip()
    else:
        await message.reply_text(
            "⚠️ Будь ласка, надішліть файл MP3, FLAC або WAV, "
            "або вставте посилання на музику (наприклад, SoundCloud, YouTube, Spotify)."
        )
        return WAITING_FOR_MUSIC

    await message.reply_text(
        "🖼 Тепер надішліть <b>обкладинку треку</b> (фото).\n"
        "Або надішліть /skip, щоб пропустити цей крок.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_IMAGE


# ──────────────────────────────────────────────
# Step 2 – Cover image (optional)
# ──────────────────────────────────────────────

async def receive_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    message = update.message

    if message.photo:
        # Use the highest-resolution version
        context.user_data["image_file_id"] = message.photo[-1].file_id
    elif message.document:
        context.user_data["image_file_id"] = message.document.file_id
    else:
        await message.reply_text(
            "⚠️ Будь ласка, надішліть фото або зображення, або /skip щоб пропустити."
        )
        return WAITING_FOR_IMAGE

    await message.reply_text(
        "🎼 Чудово! Тепер введіть <b>назву треку</b>.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_TITLE


async def skip_image(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.pop("image_file_id", None)
    await update.message.reply_text(
        "🎼 Гаразд, без обкладинки. Введіть <b>назву треку</b>.",
        parse_mode=ParseMode.HTML,
    )
    return WAITING_FOR_TITLE


# ──────────────────────────────────────────────
# Step 3 – Title
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
# Step 4 – Artist
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
# Step 5 – Optional comment
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
    caption = _submission_caption(data)
    keyboard = _approve_reject_keyboard(user.id)
    music_type = data.get("music_type")
    image_file_id = data.get("image_file_id")

    # Persist full submission so handle_approval can publish without re-parsing
    context.application.bot_data[str(user.id)] = {
        "music_type": music_type,
        "file_id": data.get("file_id"),
        "link": data.get("link"),
        "image_file_id": image_file_id,
        "title": data.get("title"),
        "artist": data.get("artist"),
        "comment": data.get("comment"),
    }

    try:
        if image_file_id:
            # Send cover photo with summary + buttons; attach music as a follow-up
            await context.bot.send_photo(
                chat_id=OWNER_CHAT_ID,
                photo=image_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )
            # Attach music file or link as a separate message so owner can preview it
            if music_type == "audio":
                await context.bot.send_audio(
                    chat_id=OWNER_CHAT_ID,
                    audio=data["file_id"],
                    caption="🎵 Музичний файл до заявки вище",
                )
            elif music_type == "document":
                await context.bot.send_document(
                    chat_id=OWNER_CHAT_ID,
                    document=data["file_id"],
                    caption="🎵 Музичний файл до заявки вище",
                )
            # link is already in the caption — no extra message needed
        else:
            # No image: send music/link directly with buttons
            if music_type == "audio":
                await context.bot.send_audio(
                    chat_id=OWNER_CHAT_ID,
                    audio=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            elif music_type == "document":
                await context.bot.send_document(
                    chat_id=OWNER_CHAT_ID,
                    document=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )
            else:  # link
                await context.bot.send_message(
                    chat_id=OWNER_CHAT_ID,
                    text=caption,
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

    if query.from_user.id != OWNER_CHAT_ID:
        await query.answer("У вас немає прав для цієї дії.", show_alert=True)
        return

    action, submitter_id_str = query.data.split(":", 1)
    submitter_id = int(submitter_id_str)

    original = query.message

    if action == "approve":
        await _publish_to_channel(context, submitter_id)
        status_line = "✅ <b>Прийнято та опубліковано на каналі.</b>"
        user_msg = "🎉 Вашу заявку <b>схвалено</b> і опубліковано на каналі!"
    else:
        status_line = "❌ <b>Відхилено.</b>"
        user_msg = "😔 На жаль, ваша заявка <b>не була відібрана</b> цього разу. Дякуємо за участь!"

    # Remove buttons and mark status on the owner's message
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

    # Clean up stored submission data
    context.application.bot_data.pop(str(submitter_id), None)


async def _publish_to_channel(context: ContextTypes.DEFAULT_TYPE, submitter_id: int) -> None:
    """Publish the approved submission to the channel using stored submission data."""
    data = context.application.bot_data.get(str(submitter_id))
    if not data:
        logger.warning("No stored submission data for user %s", submitter_id)
        return

    caption = _channel_caption(data)
    music_type = data.get("music_type")
    image_file_id = data.get("image_file_id")

    try:
        if image_file_id:
            # Post cover photo with full caption
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=image_file_id,
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            # Attach the music file below the photo post (links are already in caption)
            if music_type == "audio":
                await context.bot.send_audio(
                    chat_id=CHANNEL_ID,
                    audio=data["file_id"],
                )
            elif music_type == "document":
                await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=data["file_id"],
                )
        else:
            # No image — post music/link with caption
            if music_type == "audio":
                await context.bot.send_audio(
                    chat_id=CHANNEL_ID,
                    audio=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            elif music_type == "document":
                await context.bot.send_document(
                    chat_id=CHANNEL_ID,
                    document=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                )
            else:  # link only
                await context.bot.send_message(
                    chat_id=CHANNEL_ID,
                    text=caption,
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
