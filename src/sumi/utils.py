from pytimeparse.timeparse import timeparse
from datetime import timedelta, datetime
import os
import logging

from telegram import Message, User
from sumi.config import STATISTIC_HOURS


def get_statistic_boundary(reply_to_message: Message, args):
    if reply_to_message and reply_to_message.message_id != reply_to_message.message_thread_id:
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


def get_poll_options(args):
    return [line for line in [line.strip() for line in args.split("\"")] if line]


def get_time_delta(chat_history):
    try:
        delta = datetime.now() - datetime.fromisoformat(chat_history["messages"][0]["timestamp"])
        return timedelta(delta.days, delta.seconds)
    except:
        return None


def is_active_membership_chat(chat_id: int) -> bool:
    return str(chat_id) in os.getenv('ACTIVE_MEMBERSHIP_CHAT_IDS', '').split(",")


def is_active_chat(chat_id: int) -> bool:
    return str(chat_id) in os.getenv('ACTIVE_CHAT_IDS', '').split(",")


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


def get_logger():
    logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
    return logging.getLogger(__name__)
