import logging

from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import sumi.history.read as gch
from sumi.config import SUMMARY_HOURS_LIMIT
from sumi.summarize import summarize, create_summarize_header
from sumi.handlers.shared import fetch_chat_history, get_admin_ids
from sumi.utils import is_active_chat, get_point

logger = logging.getLogger(__name__)


async def prompt_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask prompt_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_id = update.message.chat_id
    if not is_active_chat(chat_id) and not update.message.from_user.id in await get_admin_ids(context.bot, chat_id):
        return

    chat_history, delta = await fetch_chat_history(update, context)
    if chat_history is None:
        return

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found.")
        return

    prompt = get_point(context.args)
    header = create_summarize_header(update.message.from_user, delta, prompt=prompt)
    response_message = await update.message.reply_text(header + "Дайте-ка подумать...", parse_mode=ParseMode.HTML)
    try:
        summary_generator = summarize(chat_history, delta, update.message.from_user, prompt=prompt)
        gch.updateLastCall(chat_id)
    except Exception:
        logger.exception("An error occurred while generating.")
        summary_generator = "An error occurred while generating."

    await response_message.edit_text((header + summary_generator)[0:4096], parse_mode=ParseMode.HTML)


async def summarize_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask summarize_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_id = update.message.chat_id
    if not is_active_chat(chat_id) and not update.message.from_user.id in await get_admin_ids(context.bot, chat_id):
        return

    chat_history, delta = await fetch_chat_history(update, context)
    if chat_history is None:
        return

    # time_diff = datetime.now() - datetime.fromisoformat(chat_history["summary_created_at"])
    # if os.getenv('PROD') == "True" and time_diff < timedelta(hours=SUMMARY_HOURS_LIMIT):
    #     await update.message.reply_text("Прошло меньше %d часов с последнего запроса. Все вопросы к Феликсу." % SUMMARY_HOURS_LIMIT)
    #     return

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to summarize.")
        return

    point = get_point(context.args)
    header = create_summarize_header(update.message.from_user, delta, point=point)
    response_message = await update.message.reply_text(header + "Дайте-ка подумать...", parse_mode=ParseMode.HTML)
    try:
        summary_generator = summarize(chat_history, delta, update.message.from_user, point=point)
        gch.updateLastCall(chat_id)
    except Exception:
        logger.exception("An error occurred while generating the summary.")
        summary_generator = "An error occurred while generating the summary."

    await response_message.edit_text((header + summary_generator)[0:4096], parse_mode=ParseMode.HTML)
