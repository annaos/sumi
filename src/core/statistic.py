import re
import datetime
import helpers.member as member
from helpers.util import get_logger

def _create_header(delta):
    if delta is None:
        return "Статистика после указанного сообщения\n\n"
    return "Статистика за последние %s часа\n\n" % (str(delta))


def create_statistic(chat_history, delta):
    statistic = _create_header(delta)
    messages = _convert_history(chat_history)
    if len(messages) == 0:
        return statistic + "Никто ничего не написал"

    sorted_messages = {k: v for k, v in sorted(messages.items(), key=lambda x: x[1]["count"], reverse=True)}

    place = 1
    (min, max) = _get_extremum(messages)
    for user_id, data in sorted_messages.items():
        if data["sender"] == min:
            statistic +='\U0001F64A'

        if data["sender"] == max:
            statistic +='\U0001F485'

        if place == 1:
            statistic +='\U0001F947'
        if place == 2:
            statistic +='\U0001F948'
        if place == 3:
            statistic +='\U0001F949'

        if place > 3 and data["count"] == 1:
            statistic +='\U0001F9D8'

        if data["count"] == 1:
            statistic += "%s: %d сообщение" % (data["sender"], data["count"])
        else:
            statistic += "%s: %d сообщений" % (data["sender"], data["count"])

        statistic += (" \(\~%.1f слов\)" % (data["words"] / data["count"])).replace(".",",")
        statistic +='\n'
        place += 1

    statistic += _get_tags(delta, chat_history["chat_id"], sorted_messages)
    return statistic


def _get_tags(delta: datetime, chat_id, sorted_messages):
    if delta.days < 7:
        return ""

    tags = "\n"
    members = member.get_all_members(chat_id)
    diff_members = [v for v in members if v["id"] not in sorted_messages.keys()]
    for mem in diff_members:
        if mem["username"] != None:
            tags += "@" + mem["username"].replace("_", "\\_") + " "
        elif mem["id"] != None:
            tags += "[" + mem["fullname"] + "](tg://user?id=" + str(mem["id"]) + ") "

    if len(tags) > 2:
        tags += "А вы почему молчите?"
    logger = get_logger()
    logger.info("tags: %s", tags)
    return tags


def _convert_history(chat_history):
    messages_count = {}

    for message in chat_history["messages"]:
        if message["sender_id"] in messages_count:
            messages_count[message["sender_id"]]["count"] += 1
            messages_count[message["sender_id"]]["words"] += _count_words(message["message"])
        else:
            messages_count[message["sender_id"]] = {
                "sender": message["sender"],
                "count": 1,
                "words": _count_words(message["message"])
            }

    return messages_count


def _count_words(s: str):
    return len(re.findall(r'\w+', s.strip()))


def _get_extremum(messages):
    minName = maxName = ""
    min = max = 0
    for user_id, data in messages.items():
        c = data["words"] / data["count"]
        if max < c:
            max = c
            maxName = data["sender"]
        if min == 0 or min > c:
            min = c
            minName = data["sender"]

    return (minName, maxName)