"""Conversation handlers for the Witch House Radio submission bot."""

import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from telegram.ext import (
    ContextTypes,
    ConversationHandler,
)

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
    save_track,
)


logger = logging.getLogger(__name__)


# ======================================================
# HELPERS
# ======================================================


def _is_allowed_audio(document) -> bool:

    if document is None:
        return False

    mime = (document.mime_type or "").lower()

    if mime in ALLOWED_AUDIO_MIME:
        return True

    name = (document.file_name or "").lower()

    return any(
        name.endswith(ext)
        for ext in ALLOWED_AUDIO_EXT
    )


def _submission_caption(data: dict) -> str:

    lines = [
        "🎵 <b>Нова заявка на музику</b>",
        "",
        f"🎵 <b>Трек:</b> {data.get('title', '—')}",
        f"👤 <b>Виконавець:</b> {data.get('artist', '—')}",
    ]

    if data.get("comment"):
        lines.append(
            f"💬 <b>Коментар:</b> {data['comment']}"
        )

    if data.get("link"):
        lines.append(
            f"🔗 <b>Посилання:</b> {data['link']}"
        )

    lines.extend(
        [
            "",
            f"👤 <b>Від:</b> {data.get('full_name','—')}",
            f"🆔 <code>{data.get('user_id')}</code>",
        ]
    )

    return "\n".join(lines)


def _channel_caption(data: dict) -> str:

    lines = [
        f"🎵 <b>{data.get('title','—')}</b>",
        f"👤 {data.get('artist','—')}",
    ]

    if data.get("comment"):
        lines.append(
            f"💬 {data['comment']}"
        )

    if data.get("link"):
        lines.append(
            f"🔗 {data['link']}"
        )

    return "\n".join(lines)


def _approve_reject_keyboard(submission_id: int):

    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "✅ Прийняти",
                    callback_data=f"approve:{submission_id}",
                ),
                InlineKeyboardButton(
                    "❌ Відхилити",
                    callback_data=f"reject:{submission_id}",
                ),
            ]
        ]
    )


# ======================================================
# START
# ======================================================
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    keyboard = [
        [
            InlineKeyboardButton(
                "🎵 Надіслати трек",
                callback_data="send_track"
            )
        ],
        [
            InlineKeyboardButton(
                "📢 Канал",
                url="https://t.me/witchhouse_radio"
            ),
            InlineKeyboardButton(
                "ℹ️ Допомога",
                callback_data="help"
            )
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🕯 WITCH HOUSE RADIO\n\n"
        "☽ Welcome to the Void ☾\n\n"
        "Надішліть свій трек для розгляду.",
        reply_markup=reply_markup,
    )

    return WAITING_FOR_MUSIC

    await update.message.reply_text(
        "╔════════════════════╗\n"
        "        🕯 WITCH HOUSE RADIO\n"
        "             Submit Bot\n"
        "╚════════════════════╝\n\n"
        "☽ Welcome to the Void ☾\n\n"
        "Become part of the darkness.\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "🎵 Надішліть:\n"
        "• MP3\n"
        "• FLAC\n"
        "• WAV\n"
        "• або посилання на трек\n\n"
        "━━━━━━━━━━━━━━━━━━━━\n\n"
        "The best Witch House.\n"
        "Dark Ambient.\n"
        "Underground.",
        reply_markup=reply_markup,
        parse_mode=ParseMode.HTML,
    )

    return WAITING_FOR_MUSIC

# ======================================================
# STEP 1 — MUSIC
# ======================================================


async def receive_music(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    message = update.message

    if message.audio:

        context.user_data["music_type"] = "audio"
        context.user_data["file_id"] = message.audio.file_id


    elif message.document and _is_allowed_audio(message.document):

        context.user_data["music_type"] = "document"
        context.user_data["file_id"] = message.document.file_id


    elif message.text:

        context.user_data["music_type"] = "link"
        context.user_data["link"] = message.text.strip()


    else:

        await message.reply_text(
            "⚠️ Надішліть MP3, FLAC, WAV або посилання."
        )

        return WAITING_FOR_MUSIC


    await message.reply_text(
        "🖼 Надішліть обкладинку треку "
        "або напишіть /skip.",
        parse_mode=ParseMode.HTML,
    )


    return WAITING_FOR_IMAGE

# ======================================================
# STEP 2 — IMAGE
# ======================================================

async def receive_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    message = update.message

    if message.photo:
        context.user_data["image_file_id"] = message.photo[-1].file_id

    elif message.document:
        context.user_data["image_file_id"] = message.document.file_id

    else:
        await message.reply_text(
            "⚠️ Надішліть картинку або /skip."
        )
        return WAITING_FOR_IMAGE

    await message.reply_text(
        "🎼 Введіть назву треку."
    )

    return WAITING_FOR_TITLE


# ======================================================
# STEP 2 — SKIP IMAGE
# ======================================================

async def skip_image(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    context.user_data.pop("image_file_id", None)

    await update.message.reply_text(
        "🎼 Введіть назву треку."
    )

    return WAITING_FOR_TITLE


# ======================================================
# STEP 3 — TITLE
# ======================================================

async def receive_title(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:

    title = update.message.text.strip()

    if not title:
        await update.message.reply_text(
            "Введіть назву треку."
        )
        return WAITING_FOR_TITLE

    context.user_data["title"] = title

    await update.message.reply_text(
        "🎤 Введіть виконавця."
    )

    return WAITING_FOR_ARTIST


# ──────────────────────────────────────────────
# Step 4 – Artist
# ──────────────────────────────────────────────

async def receive_artist(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    artist = update.message.text.strip()

    if not artist:
        await update.message.reply_text(
            "Введіть ім'я виконавця."
        )
        return WAITING_FOR_ARTIST

    context.user_data["artist"] = artist

    await update.message.reply_text(
        "💬 Додайте коментар або /skip."
    )

    return WAITING_FOR_COMMENT


# ──────────────────────────────────────────────
# Step 5 – Comment
# ──────────────────────────────────────────────

async def receive_comment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    context.user_data["comment"] = (
        update.message.text.strip()
    )

    return await _forward_to_owner(
        update,
        context
    )


async def skip_comment(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    context.user_data.pop(
        "comment",
        None
    )

    return await _forward_to_owner(
        update,
        context
    )


# ──────────────────────────────────────────────
# Forward submission to owner
# ──────────────────────────────────────────────

async def _forward_to_owner(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:

    user = update.effective_user

    data = context.user_data


    submission_id = add_submission(
        {
            "user_id": user.id,
            "username": user.username,
            "full_name": user.full_name,

            "music_type": data.get("music_type"),
            "file_id": data.get("file_id"),
            "image_file_id": data.get("image_file_id"),
            "link": data.get("link"),

            "title": data.get("title"),
            "artist": data.get("artist"),
            "comment": data.get("comment"),
        }
    )


    submission_data = {
        "user_id": user.id,
        "username": user.username,
        "full_name": user.full_name,

        **data,
    }


    caption = _submission_caption(
        submission_data
    )

    keyboard = _approve_reject_keyboard(
        submission_id
    )


    try:

        if data.get("image_file_id"):

            await context.bot.send_photo(
                chat_id=OWNER_CHAT_ID,
                photo=data["image_file_id"],
                caption=caption,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard,
            )


            if data.get("music_type") == "audio":

                await context.bot.send_audio(
                    chat_id=OWNER_CHAT_ID,
                    audio=data["file_id"],
                )


            elif data.get("music_type") == "document":

                await context.bot.send_document(
                    chat_id=OWNER_CHAT_ID,
                    document=data["file_id"],
                )


        else:

            if data.get("music_type") == "audio":

                await context.bot.send_audio(
                    chat_id=OWNER_CHAT_ID,
                    audio=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )


            elif data.get("music_type") == "document":

                await context.bot.send_document(
                    chat_id=OWNER_CHAT_ID,
                    document=data["file_id"],
                    caption=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )


            else:

                await context.bot.send_message(
                    chat_id=OWNER_CHAT_ID,
                    text=caption,
                    parse_mode=ParseMode.HTML,
                    reply_markup=keyboard,
                )


    except Exception:

        logger.exception(
            "Failed sending submission"
        )

        await update.message.reply_text(
            "⚠️ Помилка відправки заявки."
        )

        return ConversationHandler.END


    await update.message.reply_text(
        "✅ Заявку відправлено на розгляд!"
    )


    context.user_data.clear()

    return ConversationHandler.END
# ──────────────────────────────────────────────
# Approve / Reject
# ──────────────────────────────────────────────

async def handle_approval(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    if query.from_user.id != OWNER_CHAT_ID:
        await query.answer("Немає доступу", show_alert=True)
        return

    action, id_str = query.data.split(":")
    submission_id = int(id_str)

    submission = get_submission(submission_id)
    if not submission:
        await query.answer("Заявку не знайдено", show_alert=True)
        return

    submitter_id = submission["user_id"]

    if action == "approve":
        approve_submission(submission_id)
        await _publish_to_channel(context, submission)
        status = "\n\n✅ <b>СХВАЛЕНО та опубліковано</b>"
        message_to_user = "🎉 Ваш трек схвалено та опубліковано!"
    else:
        reject_submission(submission_id)
        status = "\n\n❌ <b>ВІДХИЛЕНО</b>"
        message_to_user = "😔 Ваш трек цього разу не пройшов відбір."

    try:
        await query.message.edit_caption(
            caption=(query.message.caption or "") + status,
            parse_mode=ParseMode.HTML,
        )
    except Exception:
        pass

    try:
        await context.bot.send_message(chat_id=submitter_id, text=message_to_user)
    except Exception:
        pass


# ──────────────────────────────────────────────
# Publish to channel
# ──────────────────────────────────────────────

async def _publish_to_channel(context: ContextTypes.DEFAULT_TYPE, submission) -> None:
    data = dict(submission)
    caption = _channel_caption(data)

    try:
        if data.get("image_file_id"):
            await context.bot.send_photo(
                chat_id=CHANNEL_ID,
                photo=data["image_file_id"],
                caption=caption,
                parse_mode=ParseMode.HTML,
            )
            if data.get("music_type") == "audio":
                await context.bot.send_audio(chat_id=CHANNEL_ID, audio=data["file_id"])
            elif data.get("music_type") == "document":
                await context.bot.send_document(chat_id=CHANNEL_ID, document=data["file_id"])
        else:
            if data.get("music_type") == "audio":
                await context.bot.send_audio(
                    chat_id=CHANNEL_ID, audio=data["file_id"],
                    caption=caption, parse_mode=ParseMode.HTML,
                )
            elif data.get("music_type") == "document":
                await context.bot.send_document(
                    chat_id=CHANNEL_ID, document=data["file_id"],
                    caption=caption, parse_mode=ParseMode.HTML,
                )
            else:
                await context.bot.send_message(
                    chat_id=CHANNEL_ID, text=caption, parse_mode=ParseMode.HTML,
                )

        save_track({
            "title": data["title"],
            "artist": data["artist"],
            "file_id": data.get("file_id"),
            "link": data.get("link"),
            "comment": data.get("comment"),
            "user_id": data.get("user_id"),
            "submission_id": data.get("id"),
        })
        logger.info("Published submission %s", data.get("id"))

    except Exception:
        logger.exception("Publish error")


# ──────────────────────────────────────────────
# /stats  (owner only)
# ──────────────────────────────────────────────

async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    data = get_stats()
    await update.message.reply_text(
        "📊 <b>Witch House Radio Bot</b>\n\n"
        f"🎵 Всього заявок: {data['total']}\n"
        f"⏳ Очікують: {data['pending']}\n"
        f"✅ Прийнято: {data['approved']}\n"
        f"❌ Відхилено: {data['rejected']}",
        parse_mode=ParseMode.HTML,
    )


# ──────────────────────────────────────────────
# /pending  (owner only)
# ──────────────────────────────────────────────

async def pending(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_user.id != OWNER_CHAT_ID:
        return
    rows = get_pending()
    if not rows:
        await update.message.reply_text("📭 Немає очікуючих заявок.")
        return
    text = "⏳ <b>Очікують:</b>\n\n"
    for row in rows[:10]:
        text += f"#{row['id']} 🎵 {row['artist']} — {row['title']}\n"
    await update.message.reply_text(text, parse_mode=ParseMode.HTML)


# ──────────────────────────────────────────────
# /cancel
# ──────────────────────────────────────────────

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    context.user_data.clear()
    await update.message.reply_text(
        "❌ Заявку скасовано.\nНадішліть /start щоб почати знову."
    )
    return ConversationHandler.END

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query
    await query.answer()

    if query.data == "send_track":
        await query.message.reply_text(
            "🎵 Надішліть ваш трек (MP3, FLAC, WAV або посилання):"
        )

    elif query.data == "help":
        await query.message.reply_text(
            "ℹ️ Допомога:\n\n"
            "Надішліть трек — бот прийме його на розгляд."
        )