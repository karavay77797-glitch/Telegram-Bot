# Music Submission Bot

A Telegram bot that lets users submit music tracks for review. The owner approves or rejects each submission via inline buttons, and approved tracks are published automatically to a Telegram channel.

## Run & Operate

- **Start the bot:** use the "Music Submission Bot" workflow (runs `cd bot && python main.py`)
- `pnpm --filter @workspace/api-server run dev` — run the API server (port 5000)
- `pnpm run typecheck` — full typecheck across all packages
- `pnpm run build` — typecheck + build all packages

## Stack

- Python 3.11 + python-telegram-bot v21.9 (async)
- pnpm workspaces, Node.js 24, TypeScript 5.9
- API: Express 5

## Where things live

```
bot/
  main.py        — entry point, Application setup & handler registration
  handlers.py    — all conversation steps + owner approval callbacks
  config.py      — env var loading & conversation state constants
  requirements.txt
```

## Bot flow

1. User sends `/start` → guided through: music file or link → title → artist → optional comment
2. Submission forwarded to owner with **Approve / Reject** buttons
3. Owner taps Approve → music published to channel; owner taps Reject → user notified

## Required Secrets

| Secret | Description |
|---|---|
| `BOT_TOKEN` | From @BotFather |
| `OWNER_CHAT_ID` | Owner's numeric Telegram ID |
| `CHANNEL_ID` | Channel username (`@chan`) or numeric ID |

## User preferences

_Populate as you build — explicit user instructions worth remembering across sessions._

## Gotchas

- `OWNER_CHAT_ID` must be a plain integer (the bot casts `os.environ["OWNER_CHAT_ID"]` to `int`)
- The bot must be an **admin** of the target channel with "Post messages" permission for publishing to work
- The owner must have started a conversation with the bot at least once before approval notifications can be sent

## Pointers

- See `bot/README.md` for quick-start instructions
- See the `pnpm-workspace` skill for workspace structure
