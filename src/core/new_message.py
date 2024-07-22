from datetime import timedelta
from telegram.ext import CallbackContext, ContextTypes

from config.common import NEW_MESSAGE_HOURS
from helpers.util import ask_ai

def new_random_message(chat_id, context: CallbackContext):
    current_jobs = context.job_queue.get_jobs_by_name(str(chat_id))
    if current_jobs:
        for job in current_jobs:
            job.schedule_removal()

    due = timedelta(hours=NEW_MESSAGE_HOURS)
    context.job_queue.run_once(alarm, due, chat_id=chat_id, name=str(chat_id))


async def alarm(context: ContextTypes.DEFAULT_TYPE) -> None:
    job = context.job
    await context.bot.send_message(job.chat_id, text=_generate_random_message())


def _generate_random_message():
    system = "Ты — участник дискуссионного чата."
    promt = "Придумай тему для горячей дискуссии. Укажи тему словами \"А что вы думаете насчёт\", а затем очень коротко выскажи свою провокативную точку зрения на неё."

    completion = ask_ai(system, promt)

    return completion.choices[0].message.content

