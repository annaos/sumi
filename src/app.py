import logging

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)

from telegram.ext import Application, ChatMemberHandler, CommandHandler, MessageHandler, filters, CallbackContext, PollHandler
from telegram import Update
from dotenv import load_dotenv
from datetime import timedelta
import os

from src.handlers.poll_handlers import (
    create_anonym_single_poll_handler,
    create_anonym_multi_poll_handler,
    create_single_poll_handler,
    create_multi_poll_handler,
    close_poll_handler,
    poll_handler,
)
from src.handlers.message_handlers import message_handler
from src.handlers.interaction_handlers import remove_handler, joke_handler, say_handler, reaction_handler
from src.handlers.stats_handlers import stats_handler, wordle_handler, green_wordle_handler, color_wordle_handler
from src.handlers.summarize_handlers import summarize_handler, prompt_handler
from src.handlers.profile_handlers import profile_handler, profile_kai_handler
from src.handlers.member_handlers import new_member, left_member, members_history_handler, chat_member_update
from src.members.reconcile import reconcile_members
from src.config import MEMBERS_RECONCILE_HOURS
from src.handlers.misc_handlers import help_handler, donate_handler, version_handler, list_handler, invite_handler, ai_usage_handler

load_dotenv()

logger = logging.getLogger(__name__)


def error_handler(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler((filters.TEXT & (~filters.COMMAND)) | filters.CAPTION, message_handler))
    app.add_handler(CommandHandler("sum", summarize_handler))
    app.add_handler(CommandHandler("summarize", summarize_handler))
    app.add_handler(CommandHandler("promt", prompt_handler))
    app.add_handler(CommandHandler("prompt", prompt_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("statt", stats_handler))
    app.add_handler(CommandHandler("stat", stats_handler))
    app.add_handler(CommandHandler("shut", joke_handler))
    app.add_handler(CommandHandler("joke", joke_handler))
    app.add_handler(CommandHandler("sumisay", say_handler))
    app.add_handler(CommandHandler("say", say_handler))
    app.add_handler(CommandHandler("reaction", reaction_handler))
    app.add_handler(CommandHandler("version", version_handler))
    app.add_handler(CommandHandler("v", version_handler))
    app.add_handler(CommandHandler("start", help_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("donate", donate_handler))
    app.add_handler(CommandHandler("poll", create_anonym_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll", create_anonym_single_poll_handler))
    app.add_handler(CommandHandler("poll_anonym", create_anonym_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll_anonym", create_anonym_single_poll_handler))
    app.add_handler(CommandHandler("poll_no_anonym", create_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll_no_anonym", create_single_poll_handler))
    app.add_handler(CommandHandler("close", close_poll_handler))
    app.add_handler(CommandHandler("stop", close_poll_handler))
    app.add_handler(CommandHandler("members_history", members_history_handler))
    app.add_handler(CommandHandler("history", members_history_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("profile_kai", profile_kai_handler))
    app.add_handler(CommandHandler("cease", remove_handler))
    app.add_handler(CommandHandler("wordle", wordle_handler))
    app.add_handler(CommandHandler("wordleG", green_wordle_handler))
    app.add_handler(CommandHandler("wordleC", color_wordle_handler))
    app.add_handler(CommandHandler("invite", invite_handler))
    app.add_handler(CommandHandler("list", list_handler))
    app.add_handler(CommandHandler("ai_usage", ai_usage_handler))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member))

    # work only if bot is an admin
    app.add_handler(ChatMemberHandler(chat_member_update, ChatMemberHandler.CHAT_MEMBER))

    app.add_handler(PollHandler(poll_handler))

    app.job_queue.run_repeating(reconcile_members,
                                interval=timedelta(hours=MEMBERS_RECONCILE_HOURS),
                                first=timedelta(minutes=5))

    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
