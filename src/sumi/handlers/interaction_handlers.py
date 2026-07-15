import logging
import random

from telegram import Update, User
from telegram.constants import ReactionEmoji
from telegram.error import BadRequest
from telegram.ext import CallbackContext

import sumi.history.read as gch
from sumi.handlers.shared import get_admin_ids, get_user
from sumi.joke_targets import add_target as add_joke_target, is_target as is_joke_target, remove_target as remove_joke_target
from sumi.jokes import generate_chain_joke_message
from sumi.reactions import add_target, is_target, remove_target
from sumi.utils import is_active_chat

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


async def add_react_target_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask add_react_target_handler with update %s", update)
    chat_id = update.message.chat_id
    if not is_active_chat(update.effective_message.chat_id) and update.message.from_user.id not in await get_admin_ids(context.bot, chat_id):
        return

    user = get_user(update.message)
    if not isinstance(user, User):
        await update.message.reply_text("Не понял, кому теперь реагировать на все сообщения. Ответь на сообщение этого человека или упомяни его.")
        return

    if is_target(chat_id, user.id):
        remove_target(chat_id, user.id)
        await update.message.reply_text("Больше не буду реагировать на все сообщения %s." % user.full_name)
    else:
        add_target(chat_id, user)
        await update.message.reply_text("Теперь буду реагировать на все сообщения %s." % user.full_name)
    await update.message.delete()


async def add_joke_target_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask add_joke_target_handler with update %s", update)
    chat_id = update.message.chat_id
    if not is_active_chat(update.effective_message.chat_id) and update.message.from_user.id not in await get_admin_ids(context.bot, chat_id):
        return

    user = get_user(update.message)
    if not isinstance(user, User):
        await update.message.reply_text("Не понял, над кем теперь шутить в каждом сообщении. Ответь на сообщение этого человека или упомяни его.")
        return

    if is_joke_target(chat_id, user.id):
        remove_joke_target(chat_id, user.id)
        await update.message.reply_text("Больше не буду шутить над каждым сообщением %s." % user.full_name)
    else:
        add_joke_target(chat_id, user)
        await update.message.reply_text("Теперь буду шутить над каждым сообщением %s." % user.full_name)
    await update.message.delete()
