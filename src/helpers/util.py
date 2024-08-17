from pytimeparse.timeparse import timeparse
from datetime import timedelta, datetime
import os
import logging

from telegram import Message, User
from config.common import AI_MODEL, STATISTIC_HOURS
import openai


def get_boundary(reply_to_message: Message, args):
    if reply_to_message:
        return (reply_to_message.message_id, None)
    try:
        (arg_str, _) = _divide_args(args)
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


def generate_joke_message(user, message: str):
    sender = get_sender(user)
    sytem = f"You are a participant in a discussion chat. Come up with a short, witty response in russian to a message from a chat member named {sender}."

    completion = ask_ai(sytem, message)

    return completion.choices[0].message.content


def is_active_chat(chat_id: int) -> bool:
    return str(chat_id) in os.getenv('ACTIVE_CHAT_IDS').split(",")


def is_active_participant(user: User) -> bool:
    name = user.full_name
    username = user.username
    return name in os.getenv('ACTIVE_NAMES').split(",") or username in os.getenv('ACTIVE_NAMES').split(",")


def get_point(args):
    (_, point) = _divide_args(args)
    return point


def _divide_args(args):
    start = True
    time = []
    point = []
    for arg in args:
        if arg[0].isdigit() and len(arg) > 1 and start:
            time.append(arg)
            continue
        else:
            start = False
        if start == False:
            point.append(arg)
    if len(time) == 0:
        while len(point) > 0 and point[-1][0].isdigit() and len(point[-1]) > 1:
            time.append(point.pop())

    return (' '.join(time), ' '.join(point))

def get_sender(user) -> str:
    sender = user.username
    if sender == "naturalist":
        return "Феликс"
    if sender == "tetianafast":
        return "Таня"
    if sender == "shachtyor":
        return "Марик"
    if sender == "arty_name":
        return "Артём"
    if sender == "Smarteclaire":
        return "Света"
    if sender == "quasado":
        return "Эльвира"
    if sender == "LadaReFa":
        return "Лада"
    if sender == "anna_os":
        return "Аня"
    if user.full_name == "iVik":
        return "Витя"
    if user.full_name == "Putyatina Tanja":
        return "Таня"
    return user.full_name


def get_logger():
    logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logging.getLogger(__name__)
