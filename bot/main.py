"""Entry point for the Music Submission Telegram Bot."""

import logging

from telegram import Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ConversationHandler,
    MessageHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    BOT_VERSION,
    WAITING_FOR_MUSIC,
    WAITING_FOR_IMAGE,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
)

from database import init_db

from handlers import (
    start,
    receive_music,
    receive_image,
    skip_image,
    receive_title,
    receive_artist,
    receive_comment,
    skip_comment,
    cancel,
    handle_approval,
    stats,
    pending,
    button_handler,
)


logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)

logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def version(update: Update, context) -> None:
    logger.info("VERSION COMMAND RECEIVED")

    await update.message.reply_text(
        f"🕯 Witch House Radio Bot\nВерсія: {BOT_VERSION}"
    )


def main() -> None:

    init_db()

    app = Application.builder().token(BOT_TOKEN).build()


    conv = ConversationHandler(
        entry_points=[
            CommandHandler("start", start),
        ],

        states={
            WAITING_FOR_MUSIC: [
                MessageHandler(
                    filters.AUDIO
                    | filters.Document.AUDIO
                    | (filters.TEXT & ~filters.COMMAND),
                    receive_music,
                )
            ],

            WAITING_FOR_IMAGE: [
                CommandHandler("skip", skip_image),
                MessageHandler(
                    filters.PHOTO | filters.Document.IMAGE,
                    receive_image,
                ),
            ],

            WAITING_FOR_TITLE: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_title,
                )
            ],

            WAITING_FOR_ARTIST: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_artist,
                )
            ],

            WAITING_FOR_COMMENT: [
                CommandHandler("skip", skip_comment),
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND,
                    receive_comment,
                )
            ],
        },

        fallbacks=[
            CommandHandler("cancel", cancel)
        ],

        allow_reentry=True,
    )


    app.add_handler(conv)


    app.add_handler(
        CommandHandler("version", version)
    )

    app.add_handler(
        CommandHandler("stats", stats)
    )

    app.add_handler(
        CommandHandler("pending", pending)
    )


    app.add_handler(
        CallbackQueryHandler(
            handle_approval,
            pattern=r"^(approve|reject):\d+$"
        )
    )


    app.add_handler(
        CallbackQueryHandler(button_handler)
    )


    logger.info(
        "🕯 WITCH HOUSE RADIO BOT v%s STARTED",
        BOT_VERSION
    )


    app.run_polling(
        allowed_updates=Update.ALL_TYPES
    )


if __name__ == "__main__":
    main()