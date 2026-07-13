import logging
from datetime import datetime

from telegram import Update
from telegram.ext import CallbackContext

import src.helpers.member as member
from src.helpers.membership import add_entry, get_last_entries
from src.helpers.util import is_active_membership_chat

logger = logging.getLogger(__name__)


async def new_member(update: Update, context: CallbackContext) -> None:
    logger.info("Ask new_member with update %s", update)
    chat_id = update.effective_message.chat_id
    new_members = update.effective_message.new_chat_members
    for new_mem in new_members:
        add_entry(chat_id, new_mem, True)
        member.add_member(chat_id, new_mem)
        if is_active_membership_chat(chat_id):
            await update.message.reply_text(f"Привет {new_mem.full_name}, надеюсь тебе понравится в нашем уютном чате. Присоединяйся к беседе! А Роза ― дура\U0001F624")


async def left_member(update: Update, context: CallbackContext) -> None:
    logger.info("Ask left_member with update %s", update)
    chat_id = update.effective_message.chat_id
    left_chat_member = update.effective_message.left_chat_member
    add_entry(chat_id, left_chat_member, False)
    member.left_member(chat_id, left_chat_member)
    if is_active_membership_chat(chat_id):
        await update.message.reply_text("Роза ― дура\U0001F624")


async def members_history_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask members_history_handler with update %s", update)
    chat_id = update.effective_message.chat_id
    count = int(" ".join(context.args)) if " ".join(context.args).isnumeric() and int(" ".join(context.args)) > 0 else 10
    history = get_last_entries(chat_id, count)
    msg = ""
    for entry in history:
        name = entry["fullname"] if entry["fullname"] else entry["username"]
        if entry["fullname"] and entry["username"]:
            name += " (aka " + entry["username"] + ")"
        state = "к нам присоединился" if entry["status"] == "join" else "нас покинул"
        time = datetime.fromisoformat(entry["timestamp"]).strftime("%d %B %Y, %H:%M:%S")

        msg += f"{time} {state} {name}\n"
    await update.message.reply_text(msg)
