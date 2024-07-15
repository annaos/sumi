from pytimeparse.timeparse import timeparse
from datetime import timedelta

from src.config.common import STATISTIC_HOURS

def text_to_timedelta(text):
    delta = timedelta(hours=STATISTIC_HOURS)
    try:
        t = timeparse(text)
        delta = timedelta(seconds=t)
    except Exception:
        pass

    return delta
