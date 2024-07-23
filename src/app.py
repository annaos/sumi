import logging
logging.basicConfig(filename='app.log',
    format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os

from core.get_chat_history import get_chat_history_by_timestamp, get_chat_history_by_message_id, updateLastCall
from core.save_message import save_message
from core.new_message import new_random_message
from core.statistic import create_statistic
from core.summarize import summarize
from core.felix_special import answer_felix
from config.common import SUMMARY_HOURS_LIMIT, VERSION
from helpers.util import get_boundary, get_time_delta

load_dotenv()

logger = logging.getLogger(__name__)

async def message_handler(update: Update, context: CallbackContext) -> None:
    is_edited = update.edited_message is not None
    message = update.edited_message if is_edited else update.message
    save_message(message, is_edited)
    new_random_message(update.effective_message.chat_id, context)

    answer = answer_felix(message, is_edited)
    if answer:
        await update.message.reply_text(answer)


async def stats_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask stats_handler with update %s", update)
    (message_id, delta) = get_boundary(update.message.reply_to_message, context.args)
    chat_id = update.message.chat_id

    try:
        if not message_id is None:
            chat_history = get_chat_history_by_message_id(chat_id, message_id)
            delta = get_time_delta(chat_history)
        else:
            timestamp = (datetime.now() - delta).isoformat()
            chat_history = get_chat_history_by_timestamp(chat_id, timestamp)
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        return

    stats_text = create_statistic(chat_history, delta)

    await update.message.reply_text(stats_text)


async def version_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask version_handler with update %s", update)
    await update.message.reply_text("My version is: " + VERSION)


async def summarize_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask summarize_handler with update %s", update)
    (message_id, delta) = get_boundary(update.message.reply_to_message, context.args)
    chat_id = update.message.chat_id

    try:
        if not message_id is None:
            chat_history = get_chat_history_by_message_id(chat_id, message_id)
            delta = get_time_delta(chat_history)
        else:
            timestamp = (datetime.now() - delta).isoformat()
            chat_history = get_chat_history_by_timestamp(chat_id, timestamp)
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        await update.message.reply_text("Something went wrong while trying to retrieve the chat history.")
        return

    time_diff = datetime.now() - datetime.fromisoformat(chat_history["summary_created_at"])
    if time_diff < timedelta(hours=SUMMARY_HOURS_LIMIT):
        await update.message.reply_text("Прошло меньше %d часов с последнего запроса. Все вопросы к Феликсу." % SUMMARY_HOURS_LIMIT)
        return

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to summarize.")
        return

    response_message = await update.message.reply_text("Generating summary... Please wait.")
    try:
        summary_generator = summarize(chat_history, delta)
        updateLastCall(chat_id)
    except Exception:
        logger.exception("An error occurred while generating the summary.")
        summary_generator = "An error occurred while generating the summary."

    await response_message.edit_text(summary_generator)

def error_handler(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), message_handler))
    app.add_handler(CommandHandler("sum", summarize_handler))
    app.add_handler(CommandHandler("summarize", summarize_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("statt", stats_handler))
    app.add_handler(CommandHandler("version", version_handler))
    app.add_handler(CommandHandler("v", version_handler))
    app.add_error_handler(error_handler)

    app.run_polling()

if __name__ == '__main__':
    main()
