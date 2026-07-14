# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

Sumi — a Russian-speaking Telegram group-chat bot (python-telegram-bot v21, async) that saves chat messages and produces AI summaries (`/sum`), statistics (`/stats`), profiles, polls, Wordle stats, and jokes via OpenAI. All user-facing bot texts are in Russian.

## Commands

```sh
# Run the bot (from repo root; requires .env, see README)
python -m src.app

# Run all tests (stdlib unittest — no pytest, no venv, system Python 3.10)
python3 -m unittest discover -s tests

# Run one file / one test
python3 -m unittest tests.test_utils
python3 -m unittest tests.test_utils.GetBoundaryTestCase.test_hours
```

Everything must run from the repo root — imports are absolute (`src.*`).

There is no linter or build step. `VERSION` in `src/config.py` is derived automatically (from `git log -1`, else `"dev"`) — never hardcode it.

## Architecture

Organized by feature, wired in `src/app.py` (handler registration + job_queue jobs). Import direction: `handlers/` → feature modules → `ai.py`/`utils.py`/`config.py`; nothing below `handlers/` touches `Update` objects.

- `src/handlers/` — all Telegram entry points. `shared.py` has `fetch_chat_history()` (resolves the "reply vs. time argument" convention used by most commands) and `get_user()` (mention/reply → User).
- `src/history/` — message persistence: `storage.py` (on-disk format), `save.py` (write path), `read.py` (read path).
- `src/members/` — member tracking: `registry.py` (current members per chat), `events.py` (join/leave log), `reconcile.py` (daily job). The registry/events split matters: state vs. event log.
- `src/summarize.py`, `src/statistic.py`, `src/jokes.py`, `src/polls.py` — one file per feature (prompts live with their feature).
- `src/ai.py` — the single OpenAI gateway (`ask_ai()`); models configured in `src/config.py`.
- `src/utils.py` — command-argument parsing and env-based chat checks only; no domain logic.

Constants and directory paths: `src/config.py`. Secrets and chat allowlists come from `.env` (see README). `is_active_chat()` returns `False` (rather than crashing) when `ACTIVE_CHAT_IDS` is unset; tests still set it via `patch.dict(os.environ, ...)` for clarity.

### Chat history storage (the part that spans multiple files)

All persistence is JSON files under `saved_data/` (gitignored). Chat history is **sharded**: each chat is a directory `chats_history/chat_<id>/` holding `meta.json` (chat_id, title, summary_created_at) plus one `messages_YYYY-MM.json` per month.

`src/history/storage.py` is the **only** module allowed to touch these files. It provides atomic writes (tmp + `os.replace`), quarantines unparseable files as `*.broken` instead of failing, and transparently migrates the legacy single-file format `chat_history_<id>.json` (renamed to `*.migrated`) on first access. Old messages are never deleted — retention/cleaning was removed deliberately.

Write path: `history/save.py` (called for every text message). Read path: `history/read.py`, whose functions return the assembled dict `{chat_id, title, ..., messages: [...]}` — everything above (handlers, `statistic.py`, `summarize.py`) only ever sees that dict shape.

### Member tracking (three redundant paths, by design)

Leaves/joins are recorded in `saved_data/members_history/members_<id>.json` via:
1. Service-message handlers (`new_member`/`left_member`) — also send the greeting replies; work without admin rights but Telegram omits these messages in groups >50 members.
2. `ChatMemberHandler` (`chat_member_update`) — reliable, but only fires where the bot is a group **admin**.
3. Daily reconcile job (`src/members/reconcile.py`) — polls `get_chat_member` for chats in `ACTIVE_CHAT_IDS` and marks silent leavers.

Because paths 1+2 can both fire for one event, dedup guards exist in `registry.add_member`, `registry.mark_member_left`, and `events.add_entry` (120 s window) — keep them intact when touching this area.

### Other conventions

- `statistic.py` output is Telegram MarkdownV2: `.`, `!`, `-`, `_`, `(`, `)` are backslash-escaped in the produced strings; broken escaping makes Telegram reject the message.
- Summaries/profiles are sent as Telegram HTML: every system prompt in `summarize.py` instructs the model to use only `<b>`/`<i>` and never `<br>`/`<p>` (Telegram rejects them) — keep that clause when editing prompts.
- Joke replies are scheduled via `job_queue` (`jokes.py`) and suppressed at night (00:00–07:30 local), rescheduled to morning.
- Tests redirect storage by patching module-level constants (`src.history.storage.HISTORY_SAVE_DIRECTORY`, `src.members.registry.HISTORY_MEMBERS_DIRECTORY`, ...) to temp dirs; integration tests in `tests/test_integration.py` use real `telegram.Message/Chat/User` objects and real files, unit tests mock the storage layer.
