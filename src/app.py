from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext
from telegram import Update
from dotenv import load_dotenv
from datetime import datetime
import os
import logging

from core.get_chat_history import get_chat_history_by_message_id, get_chat_history_by_timestamp
from core.save_message import save_message
from core.statistic import create_statistic, create_header
from core.summarize import summarize
from config.common import HOURS_LIMIT
from helpers.text_to_timedelta import text_to_timedelta

load_dotenv()

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def message_handler(update: Update, context: CallbackContext):
    """
    Save the message to the chat history.
    
    This function is called when the user sends a message.
    It saves the message to the chat history file.
    """

    is_edited = update.edited_message is not None
    message = update.edited_message if is_edited else update.message

    save_message(message, is_edited)


def chart_handler(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    time_str = update.message.text.replace('/stats', '').strip()
    delta = text_to_timedelta(time_str)

    timestamp = (datetime.now() - delta).isoformat()
    try:
        messages = get_chat_history_by_timestamp(chat_id, timestamp)
        logger.info('Chat history: %s', messages)
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        return

    chart_text = create_header(delta)
    chart_text += create_statistic(messages)
    logger.info("chart_text %s", chart_text)

    update.message.reply_text(chart_text)


def summarize_handler(update: Update, context: CallbackContext):
    """
    Generate a summary of the chat history.

    This function is called when the user sends the /summary command.
    It retrieves the chat history and sends it to the summarization model.
    Then, it sends the generated summary to the chat.
    """

    if not update.message.reply_to_message:
        update.message.reply_text("Please reply to a message with the /summarize command to get a brief summary of the messages sent after it.")
        return
    
    chat_id = update.message.chat_id
    from_message_id = update.message.reply_to_message.message_id

    try:
        messages = get_chat_history_by_message_id(chat_id, from_message_id)

        if messages == False:
            update.message.reply_text("Прошло меньше %d часов с последнего запроса. Все вопросы к Феликсу." % HOURS_LIMIT)
            return

        if len(messages) == 0:
            update.message.reply_text("No messages found to summarize. Most likely bot was just added to the chat.")
            return

        logger.info('Chat history: %s', messages)

    except Exception:
        update.message.reply_text("Something went wrong while trying to retrieve the chat history.")
        logger.exception("Error while trying to retrieve the chat history.")
        return

    response_message = update.message.reply_text("Generating summary... Please wait.")
    summary_generator = summarize(messages)
    logger.info("summary_generator %s", summary_generator)

    try:
        response_message.edit_text(summary_generator)
    except Exception:
        logger.exception("pass")
        pass


def error_handler(update: Update, context: CallbackContext):
    """
    Log the error.

    This function is called when an error occurs.
    It logs the error to the console.
    """

    logger.warning('Update "%s" caused error "%s"', update, context.error)


def main():
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    updater = Updater(TELEGRAM_BOT_TOKEN, use_context=True)

    dp = updater.dispatcher
    dp.add_handler(MessageHandler(Filters.text & (~Filters.command), message_handler))
    dp.add_handler(CommandHandler("sum", summarize_handler))
    dp.add_handler(CommandHandler("summarize", summarize_handler))
    dp.add_handler(CommandHandler("stats", chart_handler))
    dp.add_handler(CommandHandler("statt", chart_handler))
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()

if __name__ == '__main__':
    main()
