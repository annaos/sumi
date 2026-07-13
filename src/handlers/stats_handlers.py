import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

from src.statistic import create_statistic, create_wordle_statistic, create_wordle_green_statistic, create_wordle_color_statistic
from src.handlers.shared import fetch_chat_history, get_admin_ids
from src.utils import is_active_chat

logger = logging.getLogger(__name__)


async def stats_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask stats_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_id = update.message.chat_id
    if not is_active_chat(chat_id) and not update.message.from_user.id in await get_admin_ids(context.bot, chat_id):
        return

    chat_history, delta = await fetch_chat_history(update, context)
    if chat_history is None:
        return

    stats_text = create_statistic(chat_history, delta)
    logger.info("stats_text: %s", stats_text)

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN_V2)


async def wordle_handler(update: Update, context: CallbackContext) -> None:
    await general_wordle_handler(update, context, "default")


async def green_wordle_handler(update: Update, context: CallbackContext) -> None:
    await general_wordle_handler(update, context, "green")


async def color_wordle_handler(update: Update, context: CallbackContext) -> None:
    await general_wordle_handler(update, context, "color")


async def general_wordle_handler(update: Update, context: CallbackContext, mod: str = "default") -> None:
    logger.info("Ask wordle_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_history, delta = await fetch_chat_history(update, context)
    if chat_history is None:
        return

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to analyse.")
        return

    if mod == "green":
        stats_text = create_wordle_green_statistic(chat_history, delta)
    elif mod == "color":
        stats_text = create_wordle_color_statistic(chat_history, delta)
    else:
        stats_text = create_wordle_statistic(chat_history, delta)
    logger.info("wordle_stats_text: %s", stats_text)

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN_V2)
