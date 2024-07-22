from pytimeparse.timeparse import timeparse
from datetime import timedelta, datetime
import os
import logging

from telegram import Message
from config.common import AI_MODEL, STATISTIC_HOURS
import openai


def get_boundary(reply_to_message: Message, args):
    if reply_to_message:
        return (reply_to_message.message_id, None)
    try:
        arg_str = ''.join(args)
        t = timeparse(arg_str)
        delta = timedelta(seconds=t)
    except Exception:
        delta = timedelta(hours=STATISTIC_HOURS)
        pass

    return (None, delta)

def get_time_delta(chat_history):
    try:
        delta = datetime.now() - datetime.fromisoformat(chat_history["messages"][0]["timestamp"])
        return timedelta(delta.days, delta.seconds)
    except:
        return None


def ask_ai(system, promt):
    openai.api_key = os.getenv('OPENAI_TOKEN')
    completion = openai.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": promt}
        ]
    )
    logger = get_logger()
    logger.info(completion)

    return completion


def get_logger():
    logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logging.getLogger(__name__)
