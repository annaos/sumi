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


def generate_joke_message(sender: str, message: str):
    sender = sender_dictionary(sender)
    sytem = f"Ты участник дискуссионного чата. Придумай краткий и остроумный ответ на сообщение участника чата по имени {sender}."

    completion = ask_ai(sytem, message)

    return completion.choices[0].message.content


def is_active_chat(chat_id: int) -> bool:
    return str(chat_id) in os.getenv('ACTIVE_CHAT_IDS').split(",")


def is_active_participant(name: str) -> bool:
    return str(name) in os.getenv('ACTIVE_NAMES').split(",")


def sender_dictionary(sender: str) -> str:
    if sender == "Felix":
        return "Феликс"
    if sender == "Mark":
        return "Марик"
    if sender == "Tom Adler":
        return "Артём"
    if sender == "iVik":
        return "Витя"
    if sender == "Putyatina Tanja":
        return "Таня"
    if sender == "Cler":
        return "Света"
    if sender == "Elvira":
        return "Эльвира"
    if sender == "Lada":
        return "Лада"
    if sender == "Anna Os":
        return "Аня"
    return sender


def get_logger():
    logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logging.getLogger(__name__)
