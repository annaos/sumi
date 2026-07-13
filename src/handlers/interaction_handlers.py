import logging
import random

from telegram import Update
from telegram.constants import ReactionEmoji
from telegram.error import BadRequest
from telegram.ext import CallbackContext

import src.history.read as gch
from src.jokes import generate_chain_joke_message

logger = logging.getLogger(__name__)


async def remove_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask remove_handler with update %s", update)
    is_edited = update.edited_message is not None
    mes = update.message.reply_to_message

    if not is_edited and mes is not None and mes.from_user.is_bot:
        await context.bot.deleteMessage(message_id = update.message.message_id, chat_id = mes.chat_id)
        await context.bot.deleteMessage(message_id = mes.message_id, chat_id = mes.chat_id)


async def joke_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask shut_handler with update %s", update)
    is_edited = update.edited_message is not None
    mes = update.message.reply_to_message

    if not is_edited and mes is not None:
        #answer = generate_joke_message(mes.from_user, mes.text if mes.text else mes.caption)
        answer = generate_chain_joke_message(gch.get_message_history_by_message(mes))
        if answer:
            await mes.reply_text(answer)
            await update.message.delete()

    if mes is None:
        await update.message.reply_text("О чём шутить?")


async def say_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask say_handler with update %s", update)
    is_edited = update.edited_message is not None
    if update.message.reply_to_message is not None:
        mes = update.message.reply_to_message
    else:
        mes = update.message

    if not is_edited and mes is not None:
        if " " in update.message.text:
            await mes.reply_text(update.message.text.split(" ", 1)[1])
        await update.message.delete()


async def reaction_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask reaction_handler with update %s", update)
    is_edited = update.edited_message is not None
    mes = update.message.reply_to_message

    available = [e.value for e in ReactionEmoji]
    matches = [e for e in available if e in update.message.text]
    emoji = random.choice(matches) if matches else random.choice(available)

    if not is_edited:
        if mes is not None:
            try:
                await mes.set_reaction(reaction=emoji)
            except BadRequest as e:
                logger.warning(repr(e) + ": Try to set invalid reaktion: " + emoji)
        await update.message.delete()
