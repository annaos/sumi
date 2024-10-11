<a href="https://github.com/dudynets/Telegram-Summarize-Bot">
  <img src="https://user-images.githubusercontent.com/39008921/191470114-c074b17f-1c88-4af3-b089-1b14418cabf5.png" alt="drawing" width="128"/>
</a>

# Telegram Summarize Bot

<p><strong>A Telegram bot that summarizes messages from a chat.</strong></p>

> Based on development of [Oleksandr Dudynets](https://dudynets.dev)
> 
> https://github.com/dudynets/Telegram-Summarize-Bot


## Overview

When you add the bot to a chat, it start listening to all text messages and save them to a history file.
Then, when any user replies to some message with the command `/summarize` or `/sum`, 
the bot will summarize all messages that were sent since the replied message. 
Alternatively, you can use time arguments, e.g. `/sum 1h` the bot will summarise all messages sent in the last hour.

You can also generate the statistics using the `/stats` or `/stat` command. 
Here you can also do it for last time or since the replied message.

## Getting Started

### Prerequisites

- [Python](https://www.python.org/)

### Installation and Usage

1. Clone the repository
   ```sh
   git clone git@gitlab.ichbins.net:anna/sumi.git
   ```
2. Install the required packages
   ```sh
   pip install -r requirements.txt
   ```
3. Create a `.env` file in the root directory and add the following environment variables:
   ```env
   TELEGRAM_BOT_TOKEN=<your-telegram-bot-token>
   OPENAI_TOKEN=<your-openai-token>

   PROD=True
   ACTIVE_CHAT_IDS=< IDs where the bot is posting jokes>
   ACTIVE_NAMES=<names of users who often receive joke>
   MY_CHAT_ID=<your id to inform about personal messages to bot>
   ```
4. Run the bot
   ```sh
   python app.py
   ```
5. Add the bot to a group chat, send some messages and try to summarize them using the `/summarize` command.

6. Use `/help` to get a list of possible commands.

## License

Distributed under the [MIT](https://choosealicense.com/licenses/mit/) License.
See [LICENSE](LICENSE) for more information.
