from pytimeparse.timeparse import timeparse
from datetime import timedelta

from config.common import STATISTIC_HOURS
from telegram import Message


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

def _text_to_timedelta(text):
    delta = timedelta(hours=STATISTIC_HOURS)
    try:
        t = timeparse(text)
        delta = timedelta(seconds=t)
    except Exception:
        pass

    return delta
