import logging
import os
from datetime import timedelta

from telegram import Update, Chat
from telegram.ext import CallbackContext

import sumi.history.read as gch
from sumi.ai_usage import get_usage_report
from sumi.config import VERSION
from sumi.utils import get_boundary

logger = logging.getLogger(__name__)


async def help_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask help_handler with update %s", update)
    help_text = """
Меня зовут Sumi. Я умею анализировать историю чата, где я состою. Я знаю следующие комманды:
- /summarize (или просто /sum) — Я составлю краткое содержание сообщений за указанный период (не более 60 дней). Можно использовать команду как ответ на сообщение или указать временной промежуток. Если не указать, подведу итоги за последние 10 часов. Также вы можете указать мне конкретную тему, на которой я должен сконцентрироваться.
- /prompt — Напиши сам, что мне сделать на основании сообщений в чате. Можно использовать команду как ответ на сообщение или указать временной промежуток. Если не указать, подведу итоги за последние 10 часов. Также вы можете указать мне конкретную тему, на которой я должен сконцентрироваться.
- /stats — Предоставлю статистику по сообщениям за указанный период. Можно использовать как ответ на сообщение или указать временной промежуток. Если не указать, подведу статистику за последние 10 часов.
- /wordle — Покажу статистику по решению wordle за указанный период.
- /joke — Пошучу. Нужно использовать как ответ на сообщение.
- /profile — Охарактеризую выбранного участника за определённый период. Есть злой брат-близнец /profile_kai.
- /say — Скажу то, что должно быть сказано.
- /reaction — Поставлю реакцию сообщению.
- /react_target — Только для админов. Буду ставить реакцию на каждое сообщение выбранного участника (ответом на его сообщение или упоминанием). Повторный вызов на том же участнике отменяет это.
- /joke_target — Только для админов. Буду шутить над каждым сообщением выбранного участника (ответом на его сообщение или упоминанием). Повторный вызов на том же участнике отменяет это.
- /members_history — Показать историю изменения участников чата. Работает только в малениких чатах до 50 участников.
- /poll_anonym или /poll — Создам анонимный опрос с несколькими возможностями ответа.
- /singlepoll_anonym или /singlepoll — Создам анонимный опрос с только одной возможностью ответа.
- /poll_no_anonym — Создам опрос с несколькими возможностями ответа.
- /singlepoll_no_anonym — Создам опрос с только одной возможностью ответа.
- /stop и /close — Закрыть опрос. Необходимо ответить командой на сообщение с опросом (или использовать id опроса как аргумент)
- /cease — Удалю своё неудачное сообщение.
- /version — Покажу свою текущую версию.

В некоторых чатах я иногда шучу или подкалываю своих любимчиков. Если у вас есть идеи для меня, напишите мне лично.

Примеры команд:
/summarize 5d виза
/stats 1h 2m 3s
/poll "Что вы любите есть?" "макароны" "бутерброд" "суши" "пицца" "другое"
/singlepoll "Мне" "<18 лет" "18-65" ">65 лет"
/stop 5276238139109673455
/version
    """
    if update.effective_chat.type == Chat.PRIVATE:
        help_text += "\n Ещё есть команда /donate ☺"
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


async def list_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask list_handler with update %s", update)
    if update.effective_chat.type == Chat.PRIVATE and update.effective_message.chat_id == int(os.getenv("MY_CHAT_ID")):
        chats = gch.get_chat_list()
        await update.message.reply_text("\n".join(f"{key}: {value}" for key, value in chats.items()))


async def invite_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask invite_handler with update %s", update)
    if update.effective_chat.type == Chat.PRIVATE and update.effective_message.chat_id == int(os.getenv("MY_CHAT_ID")):
        chat = os.getenv("INVITE_CHAT_ID")
        link = await context.bot.create_chat_invite_link(chat)
        await update.message.reply_text(link.invite_link)


async def ai_usage_handler(update: Update, context: CallbackContext) -> None:
    logger.info("Ask ai_usage_handler with update %s", update)
    if not (update.effective_chat.type == Chat.PRIVATE and update.effective_message.chat_id == int(os.getenv("MY_CHAT_ID"))):
        return

    delta = get_boundary(context.args, timedelta(days=1))
    usage = get_usage_report(delta)
    if not usage:
        await update.message.reply_text("No AI usage recorded for this period.")
        return

    lines = ["AI usage over the last %s:" % str(delta)]
    for handler, entry in sorted(usage.items()):
        lines.append("%s: in=%d out=%d calls=%d" % (handler, entry["in_tokens"], entry["out_tokens"], entry["calls"]))
    await update.message.reply_text("\n".join(lines))
