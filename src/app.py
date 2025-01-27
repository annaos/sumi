import logging

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%H:%M:%S',
    level=logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("apscheduler.scheduler").setLevel(logging.WARNING)

from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, ContextTypes, PollHandler
from telegram import Update, Chat, User, Bot
from telegram.constants import ParseMode
from dotenv import load_dotenv
from datetime import datetime, timedelta
import os
import json

import core.get_chat_history as gch
from core.save_message import save_message, save_private_sender, get_private_sender_id
from core.poll import create_poll, save_anonym_poll_answer, stop_poll, get_poll_message_id
from core.new_message import new_random_message
from core.statistic import create_statistic
from core.summarize import summarize, profile
from core.felix_special import answer_felix
from config.common import SUMMARY_HOURS_LIMIT, VERSION, PROFILE_DAYS
from helpers.util import get_statistic_boundary, get_boundary, get_user, get_time_delta, is_active_chat, is_active_membership_chat, get_point, generate_joke_message, get_poll_options
import helpers.member as member
from helpers.membership import add_entry, get_last_entries
load_dotenv()

logger = logging.getLogger(__name__)

async def create_anonym_single_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(False, True, update, context)


async def create_anonym_multi_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(True, True, update, context)


async def create_single_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(False, False, update, context)


async def create_multi_poll_handler(update: Update, context: CallbackContext) -> None:
    await create_poll_handler(True, False, update, context)


async def create_poll_handler(multiply: bool, is_anonymous: bool, update: Update, context: CallbackContext) -> None:
    logger.info("Ask create_poll_handler with update %s", update)
    questions = get_poll_options(" ".join(context.args))
    question = questions[0] if len(questions) > 0 else "How are you?"
    options = questions[1:] if len(questions) > 2 else ["Good", "Really good", "Fantastic", "Great"]
    specification = update.message.reply_to_message.text if update.message.reply_to_message is not None else None

    message = await context.bot.send_poll(
        update.effective_chat.id,
        question,
        options,
        is_anonymous=is_anonymous,
        allows_multiple_answers=multiply
    )
    create_poll(message, specification)


async def close_poll_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask close_poll_handler with update %s", update)

    poll_id = None
    message_id = None
    if len(context.args) > 0:
        poll_id = context.args[0]
        message_id = get_poll_message_id(poll_id)
    else:
        reply_to_message = update.message.reply_to_message
        if update.message.reply_to_message is not None:
            message_id = reply_to_message.id
            poll = reply_to_message.poll
            if poll is not None:
                poll_id = poll.id

    if poll_id is None or message_id is None:
        await update.message.reply_text("Нечего закрывать")
    else:
        await context.bot.stop_poll(update.message.chat_id, int(message_id))
        stop_poll(poll_id)


async def poll_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    save_anonym_poll_answer(update.poll)


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
        id = get_private_sender_id(reply_to_message.api_kwargs["forward_sender_name"])
        if id is not None:
            await context.bot.send_message(id, text=message.text)

    if is_active_chat(update.effective_message.chat_id) and not is_edited:
        answer = answer_felix(message, is_edited)
        if answer:
            await update.message.reply_text(answer)
        else:
            new_random_message(update.effective_message.chat_id, message, context)


async def list_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask list_handler with update %s", update)
    if update.effective_chat.type == Chat.PRIVATE and update.effective_message.chat_id == int(os.getenv("MY_CHAT_ID")):
        chats = gch.get_chat_list()
        await update.message.reply_text(json.dumps(chats, indent=4))


async def shut_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask shut_handler with update %s", update)
    is_edited = update.edited_message is not None
    reply_to_message = update.message.reply_to_message

    if not is_edited and reply_to_message is not None:
        answer = generate_joke_message(reply_to_message.from_user, reply_to_message.text)
        if answer:
            await reply_to_message.reply_text(answer)

    if reply_to_message is None:
        await update.message.reply_text("О чём шутить?")


async def stats_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask stats_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_id = update.message.chat_id
    if not is_active_chat(chat_id) and not update.message.from_user.id in await _get_admin_ids(context.bot, chat_id):
        return

    (message_id, delta) = get_statistic_boundary(update.message.reply_to_message, context.args)

    try:
        if not message_id is None:
            chat_history = gch.get_chat_history_by_message_id(chat_id, message_id)
            delta = get_time_delta(chat_history)
        else:
            timestamp = (datetime.now() - delta).isoformat()
            chat_history = gch.get_chat_history_by_timestamp(chat_id, timestamp)
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        await update.message.reply_text("Something went wrong while trying to retrieve the chat history.")
        return

    stats_text = create_statistic(chat_history, delta)
    logger.info("stats_text: %s", stats_text)

    await update.message.reply_text(stats_text, parse_mode=ParseMode.MARKDOWN_V2)

async def help_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask help_handler with update %s", update)
    help_text = """
Меня зовут Sumi. Я умею анализировать историю чата, где я состою. Я знаю следующие комманды:
- /summarize (или просто /sum) — Я составлю краткое содержание сообщений за указанный период (не более 30 дней). Можно использовать команду как ответ на сообщение или указать временной промежуток. Если не указать, подведу итоги за последние 10 часов. Также вы можете указать мне конкретную тему, на которой я должен сконцентрироваться.
- /stats — Предоставлю статистику по сообщениям за указанный период. Можно использовать как ответ на сообщение или указать временной промежуток. Если не указать, подведу статистику за последние 10 часов.
- /shut — Пошучу. Нужно использовать как ответ на сообщение.
- /profile — Охарактеризую выбранного участника за определённый период.
- /members_history — Показать историю изменения участников чата. Работает только в малениких чатах до 50 участников.
- /poll_anonym или /poll — Создам анонимный опрос с несколькими возможностями ответа.
- /singlepoll_anonym или /singlepoll — Создам анонимный опрос с только одной возможностью ответа. 
- /poll_no_anonym — Создам опрос с несколькими возможностями ответа.
- /poll_no_anonym — Создам опрос с только одной возможностью ответа. 
- /stop и /close — Закрыть опрос. Необходимо ответить командой на сообщение с опросом (или использовать id опроса как аргумент)
- /version — Покажу свою текущую версию.

В некоторых чатах я иногда шучу или подкалываю своих любимчиков. Если у вас есть идеи для меня, напишите мне лично.
    
Примеры команд:
/summarize 5d Эльвира
/stats 1h 2m 3s
/poll "Что вы любите есть?" "макароны" "бутерброд" "суши" "пицца" "другое"
/singlepoll "Мне" "<18 лет" "18-65" ">65 лет"
/stop 5276238139109673455
/version
    """
    if update.effective_chat.type == Chat.PRIVATE:
        help_text += "\n Ещё есть команда /donate \u263A"
    await update.message.reply_text(help_text)


async def donate_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask donate_handler with update %s", update)
    help_text = """
 Хотите поддержать меня? Моя мама оплачивает аренду моего домика и кормит меня электричеством: www.paypal.com/paypalme/AnnaOstrovskaya
 """
    await update.message.reply_text(help_text)


async def version_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask version_handler with update %s", update)
    await update.message.reply_text("My version is: " + VERSION)


async def profile_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask profile_handler with update %s", update)
    await base_profile_handler(False, update, context)


async def profile_kai_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask profile_kai_handler with update %s", update)
    await base_profile_handler(True, update, context)


async def base_profile_handler(kai: bool, update: Update, context: CallbackContext) -> None:
    chat_id = update.message.chat_id
    user = get_user(update.message)

    if not isinstance(user, User):
        await update.message.reply_text("No user found to profile.")
        return

    delta = get_boundary(context.args, timedelta(days=PROFILE_DAYS))

    timestamp = (datetime.now() - delta).isoformat()
    chat_history = gch.get_chat_history_by_user_id(chat_id, user.id, timestamp)

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to profile.")
        return

    response_message = await context.bot.send_message(chat_id, text="Generating profiling for %s... Please wait." % user.full_name)
    try:
        profile_generator = profile(chat_history, user, delta, kai)
    except Exception:
        logger.exception("An error occurred while generating the profiling.")
        profile_generator = "An error occurred while generating the profiling."

    await response_message.edit_text(profile_generator)


async def summarize_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask summarize_handler with update %s", update)
    if update.message is None:
        logger.info("No message provided. Possible edited message. Nothing done.")
        return

    chat_id = update.message.chat_id
    if not is_active_chat(chat_id) and not update.message.from_user.id in await _get_admin_ids(context.bot, chat_id):
        return

    (message_id, delta) = get_statistic_boundary(update.message.reply_to_message, context.args)

    try:
        if not message_id is None:
            chat_history = gch.get_chat_history_by_message_id(chat_id, message_id)
            delta = get_time_delta(chat_history)
        else:
            timestamp = (datetime.now() - delta).isoformat()
            chat_history = gch.get_chat_history_by_timestamp(chat_id, timestamp)
    except Exception:
        logger.exception("Error while trying to retrieve the chat history.")
        await update.message.reply_text("Something went wrong while trying to retrieve the chat history.")
        return

    time_diff = datetime.now() - datetime.fromisoformat(chat_history["summary_created_at"])
    if os.getenv('PROD') == "True" and time_diff < timedelta(hours=SUMMARY_HOURS_LIMIT):
        await update.message.reply_text("Прошло меньше %d часов с последнего запроса. Все вопросы к Феликсу." % SUMMARY_HOURS_LIMIT)
        return

    if len(chat_history["messages"]) == 0:
        await update.message.reply_text("No messages found to summarize.")
        return

    response_message = await update.message.reply_text("Generating summary... Please wait.")
    try:
        point = get_point(context.args)
        summary_generator = summarize(chat_history, delta, update.message.from_user, point)
        gch.updateLastCall(chat_id)
    except Exception:
        logger.exception("An error occurred while generating the summary.")
        summary_generator = "An error occurred while generating the summary."

    await response_message.edit_text(summary_generator)


def error_handler(update: Update, context: CallbackContext):
    logger.warning('Update "%s" caused error "%s"', update, context.error)


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
    left_member = update.effective_message.left_chat_member
    add_entry(chat_id, left_member, False)
    member.left_member(chat_id, left_member)
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


async def _get_admin_ids(bot: Bot, chat_id: int):
    cms = await bot.getChatAdministrators(chat_id)
    result = []
    for cm in cms:
        result.append(cm.user.id)
    return result


def main():
    load_dotenv()
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(MessageHandler((filters.TEXT & (~filters.COMMAND)) | filters.CAPTION, message_handler))
    app.add_handler(CommandHandler("sum", summarize_handler))
    app.add_handler(CommandHandler("summarize", summarize_handler))
    app.add_handler(CommandHandler("stats", stats_handler))
    app.add_handler(CommandHandler("statt", stats_handler))
    app.add_handler(CommandHandler("stat", stats_handler))
    app.add_handler(CommandHandler("shut", shut_handler))
    app.add_handler(CommandHandler("version", version_handler))
    app.add_handler(CommandHandler("v", version_handler))
    app.add_handler(CommandHandler("start", help_handler))
    app.add_handler(CommandHandler("help", help_handler))
    app.add_handler(CommandHandler("donate", donate_handler))
    app.add_handler(CommandHandler("poll", create_anonym_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll", create_anonym_single_poll_handler))
    app.add_handler(CommandHandler("poll_anonym", create_anonym_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll_anonym", create_anonym_single_poll_handler))
    app.add_handler(CommandHandler("poll_no_anonym", create_multi_poll_handler))
    app.add_handler(CommandHandler("singlepoll_no_anonym", create_single_poll_handler))
    app.add_handler(CommandHandler("close", close_poll_handler))
    app.add_handler(CommandHandler("stop", close_poll_handler))
    app.add_handler(CommandHandler("members_history", members_history_handler))
    app.add_handler(CommandHandler("history", members_history_handler))
    app.add_handler(CommandHandler("profile", profile_handler))
    app.add_handler(CommandHandler("profile_kai", profile_kai_handler))
    app.add_handler(CommandHandler("list", list_handler))

    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, new_member))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, left_member))
    app.add_handler(PollHandler(poll_handler))

    app.add_error_handler(error_handler)

    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
