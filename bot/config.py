import os

BOT_TOKEN: str = os.environ["BOT_TOKEN"]
OWNER_CHAT_ID: int = int(os.environ["OWNER_CHAT_ID"])
CHANNEL_ID: str = os.environ["CHANNEL_ID"]  # e.g. "@mychannel" or "-100xxxxxxxxxx"

# Conversation states
(
    WAITING_FOR_MUSIC,
    WAITING_FOR_IMAGE,
    WAITING_FOR_TITLE,
    WAITING_FOR_ARTIST,
    WAITING_FOR_COMMENT,
) = range(5)

ALLOWED_AUDIO_MIME = {
    "audio/mpeg",       # MP3
    "audio/flac",       # FLAC
    "audio/x-flac",
    "audio/wav",        # WAV
    "audio/x-wav",
    "audio/vnd.wave",
}

ALLOWED_AUDIO_EXT = {".mp3", ".flac", ".wav"}
