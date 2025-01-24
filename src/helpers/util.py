from pytimeparse.timeparse import timeparse
from datetime import timedelta, datetime
import os
import logging

from telegram import Message, User, MessageEntity
from config.common import AI_MODEL, STATISTIC_HOURS, AI_MODEL_PRO
from helpers.member import get_real_name, get_member_by_name
import openai


def get_statistic_boundary(reply_to_message: Message, args):
    if reply_to_message:
        return (reply_to_message.message_id, None)
    delta = get_boundary(args)
    return (None, delta)


def get_boundary(args, default = timedelta(hours=STATISTIC_HOURS)):
    try:
        (arg_str, _) = _divide_args(args)
        t = timeparse(arg_str)
        delta = timedelta(seconds=t)
        return delta
    except Exception:
        return default


def get_user(message: Message) -> User|None:
    if message.reply_to_message:
        return message.reply_to_message.from_user
    for entity in message.entities:
        if entity.type == MessageEntity.TEXT_MENTION:
             return entity.user
        if entity.type == MessageEntity.MENTION :
            username = message.text[entity.offset+1:entity.offset + entity.length]
            memb = get_member_by_name(message.chat_id, username)
            if memb is not None and memb["id"] is not None:
                return User(id=memb["id"], first_name=memb["fullname"], username=memb["username"], is_bot=False)
    return None


def get_poll_options(args):
    return [line for line in [line.strip() for line in args.split("\"")] if line]


def get_time_delta(chat_history):
    try:
        delta = datetime.now() - datetime.fromisoformat(chat_history["messages"][0]["timestamp"])
        return timedelta(delta.days, delta.seconds)
    except:
        return None


def ask_ai(system, promt, model = AI_MODEL):
    openai.api_key = os.getenv('OPENAI_TOKEN')
    completion = openai.chat.completions.create(
        model=model,
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
    sytem = f"Ты участник дискуссионного чата по имени Суми. Ответь короткой шуткой на сообщение участника по имени {sender}."

    completion = ask_ai(sytem, message, AI_MODEL_PRO)

    return completion.choices[0].message.content


def is_active_membership_chat(chat_id: int) -> bool:
    return str(chat_id) in os.getenv('ACTIVE_MEMBERSHIP_CHAT_IDS').split(",")


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
    chats = os.getenv('ACTIVE_CHAT_IDS').split(",")
    if len(chats) > 0:
        return get_real_name(user, chats[0])
    return user.full_name


def get_logger():
    logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logging.getLogger(__name__)
