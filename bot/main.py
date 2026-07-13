"""Entry point for the Music Submission Telegram Bot."""

import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
)

from config import (
    BOT_TOKEN,
    WAITING_FOR_MUSIC,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
)
from handlers import (
    start,
    receive_music,
    receive_title,
    receive_artist,
    receive_comment,
    skip_comment,
    cancel,
    handle_approval,
)

logging.basicConfig(
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    app = Application.builder().token(BOT_TOKEN).build()

    # ── Submission conversation ──────────────────────────────────
    conv = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            WAITING_FOR_MUSIC: [
                MessageHandler(
                    filters.AUDIO | filters.Document.ALL | filters.TEXT & ~filters.COMMAND,
                    receive_music,
                ),
            ],
            WAITING_FOR_TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_title),
            ],
            WAITING_FOR_ARTIST: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_artist),
            ],
            WAITING_FOR_COMMENT: [
                CommandHandler("skip", skip_comment),
                MessageHandler(filters.TEXT & ~filters.COMMAND, receive_comment),
            ],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True,
    )

    app.add_handler(conv)

    # ── Owner approve / reject buttons ──────────────────────────
    app.add_handler(CallbackQueryHandler(handle_approval, pattern=r"^(approve|reject):\d+$"))

    logger.info("Bot is starting — polling for updates…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
