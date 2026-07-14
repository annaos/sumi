import logging
import os

from telegram import Update, Chat
from telegram.ext import CallbackContext

from src.jokes import answer_lucky
from src.jokes import new_delay_message
from src.history.save import save_message, save_private_sender, resolve_reply_target_id
from src.reactions import maybe_react
from src.utils import is_active_chat

logger = logging.getLogger(__name__)


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

    if is_active_chat(update.effective_message.chat_id) and not is_edited:
        await react_lucky(message)

        answer = answer_lucky(message, is_edited)
        if answer:
            await update.message.reply_text(answer)
        else:
            new_delay_message(update.effective_message.chat_id, message, context)
