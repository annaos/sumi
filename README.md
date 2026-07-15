<a href="https://github.com/dudynets/Telegram-Summarize-Bot">
  <img src="https://user-images.githubusercontent.com/39008921/191470114-c074b17f-1c88-4af3-b089-1b14418cabf5.png" alt="drawing" width="128"/>
</a>

# Sumi — Telegram Chat Bot

<p><strong>A Russian-speaking Telegram group-chat bot that saves chat messages and turns them into AI summaries, statistics, and more.</strong></p>

> Originally based on [Telegram Summarize Bot](https://github.com/dudynets/Telegram-Summarize-Bot) by [Oleksandr Dudynets](https://dudynets.dev), since then heavily extended.

## Features

Once added to a group chat, Sumi listens to all text messages and stores them in a local history. On top of that history she offers:

- **Summaries** — `/sum` (or `/summarize`) summarizes what was discussed. Reply to a message to summarize everything since it, pass a time range (`/sum 2h`), and/or name a topic to focus on (`/sum 5d виза`). Defaults to the last 10 hours. `/prompt <instruction>` runs your own instruction over the chat history instead of the standard summary.
- **Statistics** — `/stats` shows who wrote how many messages (with medals 🥇 and average message length). `/wordle`, `/wordleG`, `/wordleC` rank the chat's Wordle players by attempts, green and colored squares.
- **Profiles** — `/profile` describes a chat member based on their messages; `/profile_kai` is the blunt evil twin.
- **Polls** — `/poll`, `/singlepoll` (anonymous), `/poll_no_anonym`, `/singlepoll_no_anonym`; close with `/close` or `/stop`. Example: `/poll "Что вы любите есть?" "макароны" "суши" "другое"`.
- **Fun** — `/joke` (reply to a message), `/say`, `/reaction`, and spontaneous jokes in configured chats (never at night, 00:00–07:30).
- **Member tracking** — greets newcomers, records joins/leaves (`/history`), and detects members who left silently: via `chat_member` updates and a daily reconciliation job that asks Telegram about each known member of the active chats.
- `/help` shows the full command list, `/version` the running version.

## Getting Started

### Prerequisites

- [Python](https://www.python.org/) 3.10+

### Installation and Usage

1. Clone the repository
   ```sh
   git clone git@gitlab.ichbins.net:anna/sumi.git
   ```
2. Install the package (editable install, so code changes take effect immediately)
   ```sh
   pip install -e .
   ```
3. Create a `.env` file in the root directory:
   ```env
   TELEGRAM_BOT_TOKEN=<your telegram bot token>
   OPENAI_TOKEN=<your OpenAI API key>

   PROD=True
   # Chats where the bot's core commands are open to non-admins (comma-separated chat IDs)
   ACTIVE_CHAT_IDS=-100123,-100456
   # Chats where the bot jokes and reacts spontaneously (comma-separated chat IDs)
   ACTIVE_JOKE_CHAT_IDS=-100123,-100456
   # Chats where the bot tracks members joining/leaving (comma-separated chat IDs)
   ACTIVE_MEMBERSHIP_CHAT_IDS=-100123
   # The one chat where the bot additionally greets joining/leaving members (comma-separated chat IDs)
   ACTIVE_GREETING_CHAT_IDS=-100124
   # Your own chat ID — private messages to the bot are forwarded here
   MY_CHAT_ID=12345
   ```
4. Run the bot (from the repository root)
   ```sh
   python -m sumi.app
   ```
5. Add the bot to a group chat, send some messages and try `/sum`.

> **Note:** to detect leaving members reliably (including in groups with more than 50 members, where Telegram sends no "user left" service messages), the bot should be an **administrator** of the group. Without admin rights the daily reconciliation job still corrects the member list within a day.

## Data Storage

All data lives as JSON files under `saved_data/` (git-ignored), no database needed:

- `chats_history/chat_<id>/` — one directory per chat: `meta.json` plus one `messages_YYYY-MM.json` file per month. Files are written atomically; an unparseable file is set aside as `*.broken` and the bot keeps working. Old single-file histories (`chat_history_<id>.json`) are migrated automatically on first access.
- `members_history/` — current members and the join/leave log per chat.
- `polls/` — open polls.

## Development

```sh
# run all tests
python3 -m unittest discover -s tests

# run a single test file or test
python3 -m unittest tests.test_util
python3 -m unittest tests.test_util.GetBoundaryTestCase.test_hours
```

The code lives in `src/sumi/`, organized by feature: `handlers/` (all Telegram commands), `history/` (message storage), `members/` (member tracking), plus one module per feature (`summarize.py`, `statistic.py`, `jokes.py`, `polls.py`) on top of shared `ai.py`, `utils.py`, and `config.py`. See `CLAUDE.md` for architecture details and conventions.

## License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License.
See [LICENSE](LICENSE) for more information.
