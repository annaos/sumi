import logging
import os
import random

from telegram import Update, Chat
from telegram.constants import ReactionEmoji
from telegram.error import BadRequest
from telegram.ext import CallbackContext

from src.core.felix_special import answer_felix
from src.core.new_message import new_delay_message
from src.core.save_message import save_message, save_private_sender, get_private_sender_id
from src.helpers.util import is_active_chat

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
        id = None
        if "forward_sender_name" in reply_to_message.api_kwargs:
            id = get_private_sender_id(reply_to_message.api_kwargs["forward_sender_name"])
        elif "forward_from" in reply_to_message.api_kwargs:
            id = reply_to_message.api_kwargs["forward_from"]["id"]
        if id is not None:
            await context.bot.send_message(id, text=message.text)

    if is_active_chat(update.effective_message.chat_id) and not is_edited:
        if random.random() < 0.05:
            available = [e.value for e in ReactionEmoji]
            emoji = random.choice(available)
            try:
              await message.set_reaction(reaction=emoji)
            except BadRequest as e:
                logger.error(repr(e) + ": Try to set invalid reaktion: " + emoji)
                await message.set_reaction(reaction=ReactionEmoji.HEART_WITH_ARROW)

        answer = answer_felix(message, is_edited)
        if answer:
            await update.message.reply_text(answer)
        else:
            new_delay_message(update.effective_message.chat_id, message, context)
