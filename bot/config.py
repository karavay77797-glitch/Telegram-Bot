import os
from pathlib import Path


# ==========================================
# Telegram
# ==========================================

BOT_TOKEN: str = os.environ["BOT_TOKEN"]

OWNER_CHAT_ID: int = int(
    os.environ["OWNER_CHAT_ID"]
)

CHANNEL_ID: str = os.environ["CHANNEL_ID"]


# ==========================================
# Paths
# ==========================================

BASE_DIR = Path(__file__).resolve().parent

DATABASE_PATH = BASE_DIR / "database.db"

LOGS_DIR = BASE_DIR / "logs"
BACKUP_DIR = BASE_DIR / "backups"

LOGS_DIR.mkdir(
    exist_ok=True
)

BACKUP_DIR.mkdir(
    exist_ok=True
)


# ==========================================
# Conversation states
# ==========================================

(
    WAITING_FOR_MUSIC,
    WAITING_FOR_IMAGE,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
) = range(5)


# ==========================================
# Allowed audio
# ==========================================

ALLOWED_AUDIO_MIME = {
    "audio/mpeg",
    "audio/flac",
    "audio/x-flac",
    "audio/wav",
    "audio/x-wav",
    "audio/vnd.wave",
}


ALLOWED_AUDIO_EXT = {
    ".mp3",
    ".flac",
    ".wav",
}


# ==========================================
# Allowed images
# ==========================================

ALLOWED_IMAGE_EXT = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
}


# ==========================================
# Limits
# ==========================================

MAX_COMMENT_LENGTH = 500
MAX_TITLE_LENGTH = 150
MAX_ARTIST_LENGTH = 150


# ==========================================
# Anti spam
# ==========================================

SUBMISSION_COOLDOWN = 60


# ==========================================
# Default hashtags
# ==========================================

DEFAULT_HASHTAGS = [
    "#witchhouse",
    "#darkwave",
    "#electronic",
]


# ==========================================
# Statuses
# ==========================================

STATUS_PENDING = "pending"
STATUS_APPROVED = "approved"
STATUS_REJECTED = "rejected"


# ==========================================
# Version
# ==========================================

BOT_VERSION = "2.0"