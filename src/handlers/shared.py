import logging
from datetime import datetime

from telegram import Bot, Message, MessageEntity, Update, User
from telegram.ext import CallbackContext

import src.history.read as gch
from src.members.registry import get_member_by_name
from src.utils import get_statistic_boundary, get_time_delta

logger = logging.getLogger(__name__)


def get_user(message: Message) -> User|None:
    if message.reply_to_message:
        return message.reply_to_message.from_user
    for entity in message.entities:
        if entity.type == MessageEntity.TEXT_MENTION:
             return entity.user
        if entity.type == MessageEntity.MENTION :
            username = message.text[entity.offset+1:entity.offset + entity.length]
            memb = get_member_by_name(message.chat_id, username)
            if memb is not None and memb["id"] is not None:
                return User(id=memb["id"], first_name=memb["fullname"], username=memb["username"], is_bot=False)
    return None


async def fetch_chat_history(update: Update, context: CallbackContext):
    chat_id = update.message.chat_id
    (message_id, delta) = get_statistic_boundary(update.message.reply_to_message, context.args)

    try:
        if message_id is not None:
            chat_history = gch.get_chat_history_by_message_id(chat_id, message_id)
            delta = get_time_delta(chat_history)
        else:
            timestamp = (datetime.now() - delta).isoformat()
            chat_history = gch.get_chat_history_by_timestamp(chat_id, timestamp)
    except FileNotFoundError:
        await update.message.reply_text("There is no chat history yet. Maybe I was just added to the chat.")
        return None, None
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        await update.message.reply_text("Something went wrong while trying to retrieve the chat history.")
        return None, None

    return chat_history, delta


async def get_admin_ids(bot: Bot, chat_id: int):
    cms = await bot.getChatAdministrators(chat_id)
    return [cm.user.id for cm in cms]
