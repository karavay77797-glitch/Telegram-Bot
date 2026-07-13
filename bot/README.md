# Music Submission Bot

A Telegram bot that lets users submit music to a channel, with owner approval before publishing.

## Features

- Guides users through a step-by-step submission flow
- Accepts MP3, FLAC, WAV files **or** a music link (SoundCloud, YouTube, Spotify, etc.)
- Collects track title, artist name, and an optional comment
- Forwards each submission to the bot owner with **Approve / Reject** buttons
- On approval, automatically publishes the music to the configured Telegram channel
- Notifies the submitter of the decision either way

## Environment Variables (Secrets)

| Variable | Description |
|---|---|
| `BOT_TOKEN` | Bot token from [@BotFather](https://t.me/BotFather) |
| `OWNER_CHAT_ID` | Your personal Telegram chat ID (forward any message to [@userinfobot](https://t.me/userinfobot) to find it) |
| `CHANNEL_ID` | Channel username (`@mychannel`) or numeric ID (`-100xxxxxxxxxx`) |

## Running

```bash
cd bot
pip install -r requirements.txt
python main.py
```

## User Commands

| Command | Action |
|---|---|
| `/start` | Begin a new submission |
| `/skip` | Skip the optional comment step |
| `/cancel` | Cancel the current submission |
