import logging

from telegram import Update
from telegram.ext import CallbackContext

from src.polls import create_poll, save_anonym_poll_answer, stop_poll, get_poll_message_id
from src.utils import get_poll_options

logger = logging.getLogger(__name__)


async def create_anonym_single_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(False, True, update, context)


async def create_anonym_multi_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(True, True, update, context)


async def create_single_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(False, False, update, context)


async def create_multi_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(True, False, update, context)


async def create_poll_handler(multiply: bool, is_anonymous: bool, update: Update, context: CallbackContext) -> None:
    logger.info("Ask create_poll_handler with update %s", update)
    questions = get_poll_options(" ".join(context.args))
    question = questions[0] if len(questions) > 0 else "How are you?"
    options = questions[1:] if len(questions) > 2 else ["Good", "Really good", "Fantastic", "Great"]
    specification = update.message.reply_to_message.text if update.message.reply_to_message is not None else None

    message = await context.bot.send_poll(
        update.effective_chat.id,
        question,
        options,
        is_anonymous=is_anonymous,
        allows_multiple_answers=multiply
    )
    create_poll(message, specification)


async def close_poll_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask close_poll_handler with update %s", update)

    poll_id = None
    message_id = None
    if len(context.args) > 0:
        poll_id = context.args[0]
        message_id = get_poll_message_id(poll_id)
    else:
        reply_to_message = update.message.reply_to_message
        if update.message.reply_to_message is not None:
            message_id = reply_to_message.id
            poll = reply_to_message.poll
            if poll is not None:
                poll_id = poll.id

    if poll_id is None or message_id is None:
        await update.message.reply_text("Нечего закрывать")
    else:
        await context.bot.stop_poll(update.message.chat_id, int(message_id))
        stop_poll(poll_id)


async def poll_handler(update: Update, context: CallbackContext) -> None:
    save_anonym_poll_answer(update.poll)
