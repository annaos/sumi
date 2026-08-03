import logging
from datetime import datetime, timedelta

from telegram import Update, User
from telegram.constants import ParseMode
from telegram.ext import CallbackContext

import sumi.history.read as gch
from sumi.config import PROFILE_DAYS
from sumi.summarize import profile
from sumi.handlers.shared import get_admin_ids, get_user
from sumi.utils import get_boundary, is_active_chat, get_time_delta

logger = logging.getLogger(__name__)


async def profile_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask profile_handler with update %s", update)
    await base_profile_handler(False, update, context)


async def profile_kai_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask profile_kai_handler with update %s", update)
    await base_profile_handler(True, update, context)


async def base_profile_handler(kai: bool, update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user = get_user(update.message)

    if not is_active_chat(chat_id) and not update.message.from_user.id in await get_admin_ids(context.bot, chat_id):
        return

    if not isinstance(user, User):
        await update.message.reply_text("No user found to profile.")
        return

    (message_id, delta) = get_boundary(update.message.reply_to_message, context.args, timedelta(days=PROFILE_DAYS))

    if message_id is not None:
        chat_history = gch.get_chat_history_by_message_id(chat_id, message_id)
        delta = get_time_delta(chat_history)
    else:
        timestamp = (datetime.now() - delta).isoformat()
        chat_history = gch.get_chat_history_by_timestamp(chat_id, timestamp)

    chat_history = gch.filter_chat_history_by_user_id(chat_history, user.id)

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to profile.")
        return

    response_message = await context.bot.send_message(chat_id, text="Generating profiling for %s... Please wait." % user.full_name)
    try:
        profile_generator = profile(chat_history, user, delta, kai)
    except Exception:
        logger.exception("An error occurred while generating the profiling.")
        profile_generator = "An error occurred while generating the profiling."

    await response_message.edit_text(profile_generator, parse_mode=ParseMode.HTML)
