# tg-secretary

Telegram Business secretary bot. Auto-replies to incoming business messages with Google Gemini, on behalf of the account owner. Supports DND with quiet hours, per-chat AI context, per-chat reply cooldown, media-message acknowledgment, and an optional SOCKS5 proxy for Telegram and Gemini.

## Requirements

- Python 3.12+
- Telegram Premium (required to connect a business bot)
- Google Gemini API key
- Optional: SOCKS5 proxy if Telegram or Gemini are blocked on your network

## Telegram setup

1. Create a bot in [@BotFather](https://t.me/BotFather). In Bot Settings, enable **Business Mode**.
2. In your Telegram client: Settings → Business → Chatbots → add the bot. Grant it the "Reply to messages" right.
3. Get a Gemini API key at https://aistudio.google.com/apikey.
4. Find your numeric Telegram user id (e.g. via [@userinfobot](https://t.me/userinfobot)).

## Install

**Linux / macOS**
```bash
python3 -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env
```

**Windows**
```powershell
python -m venv venv
venv\Scripts\python.exe -m pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` with the values from the Telegram setup step.

## Configuration

| Variable             | Required | Default              | Notes |
|----------------------|----------|----------------------|-------|
| `BOT_TOKEN`          | yes      |                      | From @BotFather |
| `GEMINI_API_KEY`     | yes      |                      | From Google AI Studio |
| `OWNER_USER_ID`      | yes      |                      | Your Telegram numeric id |
| `GEMINI_MODEL`       | no       | `gemini-2.5-flash`   | Any Gemini model name |
| `DB_PATH`            | no       | `data/bot.db`        | SQLite file path |
| `TZ_OFFSET_MIN`      | no       | `0`                  | Local-time offset for `/quiet`, minutes from UTC |
| `PROXY_URL`          | no       | (none)               | e.g. `socks5://127.0.0.1:10808` |
| `REPLY_COOLDOWN_MIN` | no       | `0`                  | Skip auto-reply if last reply to that chat was within N minutes |

## Run

**Linux / macOS**
```bash
venv/bin/python main.py
```

**Windows**
```powershell
venv\Scripts\python.exe main.py
```

## Owner commands

DM these to the bot (only the configured owner is allowed).

| Command                 | Effect |
|-------------------------|--------|
| `/dnd on`               | Enable auto-reply (master switch) |
| `/dnd off`              | Disable auto-reply |
| `/quiet HH:MM HH:MM`    | Auto-reply only inside this local-time window (wraps midnight) |
| `/quiet off`            | Auto-reply any time (when `/dnd on`) |
| `/rules <text>`         | Set the global AI context |
| `/here <text>`          | Set AI context for the active chat (the last contact who messaged) |
| `/here off`             | Clear the active chat's per-chat context |
| `/status`               | Show DND state, quiet window, active chat, global context |
| `/help`                 | Show the command list |

## Tests

```bash
venv/bin/python -m pytest   # Linux/macOS
venv\Scripts\python.exe -m pytest   # Windows
```

## Project layout

```
main.py              entry point: wires Bot, Dispatcher, services, routers
src/config.py        pydantic-settings env config
src/db/              SQLAlchemy models + async SQLite repository
src/services/ai.py   Gemini client wrapper (supports SOCKS5)
src/services/dnd.py  master switch + quiet-hours window
src/services/filter.py    minimal spam guard
src/services/responder.py orchestrates incoming -> AI -> reply
src/handlers/        aiogram routers (commands, business, connection)
tests/               pytest suite
```
