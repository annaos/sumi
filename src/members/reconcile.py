import logging

from telegram import ChatMember, User
from telegram.error import TelegramError
from telegram.ext import ContextTypes

import src.members.registry as member
from src.members.events import add_entry
from src.utils import is_active_chat

logger = logging.getLogger(__name__)


async def reconcile_members(context: ContextTypes.DEFAULT_TYPE) -> None:
    for chat_id in member.get_chat_ids():
        if not is_active_chat(chat_id):
            continue
        await _reconcile_chat(context, chat_id)


async def _reconcile_chat(context, chat_id):
    for memb in member.get_all_members(chat_id):
        if memb["id"] is None:
            logger.warning("Cannot verify member %s in chat %s: no user id, check manually",
                           memb["fullname"], chat_id)
            continue

        try:
            chat_member = await context.bot.get_chat_member(chat_id, memb["id"])
        except TelegramError as error:
            logger.warning("Cannot verify member %s in chat %s: %s", memb["fullname"], chat_id, error)
            continue

        if chat_member.status in (ChatMember.LEFT, ChatMember.BANNED):
            logger.info("Member %s left chat %s unnoticed, marking as left", memb["fullname"], chat_id)
            member.mark_member_left(chat_id, memb["id"])
            user = User(id=memb["id"], first_name=memb["fullname"], username=memb["username"], is_bot=False)
            add_entry(chat_id, user, False)
