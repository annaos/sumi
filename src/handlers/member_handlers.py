import logging
from datetime import datetime

from telegram import ChatMember, ChatMemberUpdated, Update
from telegram.ext import CallbackContext

import src.helpers.member as member
from src.helpers.membership import add_entry, get_last_entries
from src.helpers.util import is_active_membership_chat

logger = logging.getLogger(__name__)


def _extract_status_change(chat_member_update: ChatMemberUpdated):
    status_change = chat_member_update.difference().get("status")
    old_is_member, new_is_member = chat_member_update.difference().get("is_member", (None, None))

    if status_change is None:
        return None

    old_status, new_status = status_change
    was_member = old_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (old_status == ChatMember.RESTRICTED and old_is_member is True)
    is_member = new_status in [
        ChatMember.MEMBER,
        ChatMember.OWNER,
        ChatMember.ADMINISTRATOR,
    ] or (new_status == ChatMember.RESTRICTED and new_is_member is True)

    return was_member, is_member


async def chat_member_update(update: Update, context: CallbackContext) -> None:
    logger.info("Ask chat_member_update with update %s", update)
    change = _extract_status_change(update.chat_member)
    if change is None:
        return

    was_member, is_member = change
    chat_id = update.chat_member.chat.id
    user = update.chat_member.new_chat_member.user

    if not was_member and is_member:
        add_entry(chat_id, user, True)
        member.add_member(chat_id, user)
    elif was_member and not is_member:
        add_entry(chat_id, user, False)
        member.left_member(chat_id, user)


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
