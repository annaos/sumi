import logging
import os

from telegram import Update, Chat, Message, MessageEntity
from telegram.ext import CallbackContext

from sumi.jokes import answer_lucky, generate_chain_joke_message
from sumi.jokes import new_delay_message
from sumi.history.save import save_message, save_private_sender, resolve_reply_target_id
import sumi.history.read as gch
from sumi.reactions import react_lucky
from sumi.utils import is_active_joke_chat

logger = logging.getLogger(__name__)


def _is_bot_addressed(message: Message, bot) -> bool:
    reply = message.reply_to_message
    if reply is not None and reply.from_user is not None and reply.from_user.id == bot.id:
        return True
    for entity in message.entities:
        if entity.type == MessageEntity.MENTION:
            mention = message.text[entity.offset:entity.offset + entity.length]
            if mention.lower() == f"@{bot.username}".lower():
                return True
    return False


async def message_handler(update: Update, context: CallbackContext) -> None:
    is_edited = update.edited_message is not None
    message = update.edited_message if is_edited else update.message
    save_message(message, is_edited)
    reply_to_message = message.reply_to_message
    root_chat_id = int(os.getenv("MY_CHAT_ID"))

    if update.effective_chat.type == Chat.PRIVATE and message.chat_id != root_chat_id:
        save_private_sender(message.chat_id, message.from_user.full_name, message.from_user.username)
        await update.message.forward(root_chat_id)
    elif update.effective_chat.type == Chat.PRIVATE and message.chat_id == root_chat_id and reply_to_message is not None:
        id = resolve_reply_target_id(reply_to_message)
        if id is not None:
            await context.bot.send_message(id, text=message.text)
    elif not is_edited and _is_bot_addressed(message, context.bot):
        answer = generate_chain_joke_message(gch.get_message_history_by_message(message), message.chat_id)
        if answer:
            await update.message.reply_text(answer)
    elif is_active_joke_chat(update.effective_message.chat_id) and not is_edited:
        await react_lucky(message)

        answer = answer_lucky(message, is_edited)
        if answer:
            await update.message.reply_text(answer)
        else:
            new_delay_message(update.effective_message.chat_id, message, context)
