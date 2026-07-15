import logging
import random
from datetime import datetime, timedelta, time

from telegram import Message
from telegram.ext import CallbackContext, ContextTypes

from sumi.ai import ask_ai
from sumi.config import ACTIVE_ANSWER_FREQUENCY, ALL_ANSWER_FREQUENCY, AI_MODEL_PRO, NEW_MESSAGE_MINUTES
from sumi.joke_targets import is_target
from sumi.members.registry import get_sender
import sumi.history.read as gch

logger = logging.getLogger(__name__)


JOKE_RULES = """
Правила:
- Одно-два предложения. Не объясняй шутку, не здоровайся и не бери ответ в кавычки.
- Пиши обычным текстом: без разметки, без HTML-тегов.
- Избегай шуток про Wi-Fi и кофе.
"""


def generate_joke_message(user, message: str):
    sender = get_sender(user)
    system = f"""
Ты — Суми, остроумный участник группового чата. Тебе дадут сообщение участника по имени {sender}.
Ответь на него короткой шуткой:
- Шути по сути сообщения, а не общими фразами. Можно по-злому подколоть {sender}.
{JOKE_RULES}"""

    completion = ask_ai(system, message, "joke", AI_MODEL_PRO)

    return completion.choices[0].message.content


def generate_chain_joke_message(messages_history):
    system = f"""
Ты — Суми, остроумный участник группового чата. Тебе дадут цепочку сообщений, по одному в строке, в формате «отправитель: сообщение».
Ответь на эту беседу короткой шуткой:
- Шути по сути обсуждения, не называя имён участников.
{JOKE_RULES}"""

    messages = ""
    for message in messages_history:
        if message != None:
            messages += "%s: %s \n" % (message["sender"], message["message"])

    completion = ask_ai(system, messages, "joke_chain", AI_MODEL_PRO)

    return completion.choices[0].message.content


def answer_lucky(message: Message, is_edited: bool):
    if is_edited == True:
        return None
    is_lucky_message = random.random() < ALL_ANSWER_FREQUENCY
    is_target_message = is_target(message.chat_id, message.from_user.id) and random.random() < ACTIVE_ANSWER_FREQUENCY
    if is_lucky_message or is_target_message:
        return generate_joke_message(message.from_user, message.text if message.text else message.caption)
    return None


def new_delay_message(chat_id, message: Message, context: CallbackContext):
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

    due = timedelta(minutes=NEW_MESSAGE_MINUTES)
    if _is_time_at_night(datetime.now() + due):
        due = _get_due_till_morning(datetime.now())
    context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id), data=message)


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    message = job.data
    await context.bot.send_message(job.chat_id, text=generate_chain_joke_message(gch.get_message_history_by_message(message)))


startH = 0
startM = 0
endH = 7
endM = 30


def _is_time_at_night(x):
    start = time(startH, startM, 0)
    end = time(endH, endM, 0)
    x_time = x.astimezone().time()

    if start <= end:
        return start <= x_time <= end
    else:
        return start <= x_time or x_time <= end


def _get_due_till_morning(x):
    now = x
    end = time(endH, endM, 0)

    if x.astimezone().time() <= end:
        end = x.replace(hour=endH, minute=endM)
    else:
        end = (x + timedelta(days=1)).replace(hour=endH, minute=endM)

    return end - now
