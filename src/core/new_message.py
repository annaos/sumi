import logging
from datetime import datetime,timedelta, time

from telegram.ext import CallbackContext, ContextTypes
from telegram import Message

from config.common import NEW_MESSAGE_MINUTES
from helpers.util import ask_ai, generate_joke_message

logger = logging.getLogger(__name__)

def new_random_message(chat_id, message: Message, context: CallbackContext):
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
    await context.bot.send_message(job.chat_id, text=generate_joke_message(message.from_user, message.text))


# generate only joke messages at the moment
def _generate_new_theme_message():
    system = "Ты — участник дискуссионного чата по имени Суми."
    promt = "Придумай тему для горячей дискуссии. Укажи тему словами \"А что вы думаете насчёт\", а затем очень коротко выскажи свою провокативную точку зрения на неё."

    completion = ask_ai(system, promt)

    return completion.choices[0].message.content


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
