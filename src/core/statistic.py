import re
import datetime
import helpers.membership as membership
from helpers.util import get_logger

def _create_header(delta):
    if delta is None:
        return "Статистика после указанного сообщения\n\n"
    return "Статистика за последние %s часа\n\n" % (str(delta))


def create_statistic(chat_history, delta):
    statistic = _create_header(delta)
    (messages, words) = _convert_history(chat_history)
    if len(messages) == 0:
        return statistic + "Никто ничего не написал."

    sorted_messages = {k: v for k, v in sorted(messages.items(), key=lambda x: x[1], reverse=True)}

    place = 1
    (min, max) = _get_extremum(messages, words)
    for user, count in sorted_messages.items():
        if user == min:
            statistic +='\U0001F64A'

        if user == max:
            statistic +='\U0001F485'

        if place == 1:
            statistic +='\U0001F947'
        if place == 2:
            statistic +='\U0001F948'
        if place == 3:
            statistic +='\U0001F949'

        if place > 3 and count == 1:
            statistic +='\U0001F9D8'

        if count == 1:
            statistic += "%s: %d сообщение" % (user, count)
        else:
            statistic += "%s: %d сообщений" % (user, count)

        statistic += " (%d слов)" % (words[user])
        statistic +='\n'
        place += 1

    statistic += _get_tags(delta, chat_history["chat_id"], sorted_messages)
    return statistic


def _get_tags(delta: datetime, chat_id, sorted_messages):
    tags = "\n"
    if delta.days < 7:
        return ""

    members = membership.get_all_members(chat_id)
    diff_members = [v for v in members if v["fullname"] not in sorted_messages]
    for mem in diff_members:
        if mem["username"] != None:
            tags += "@" + mem["username"] + " "
        elif mem["id"] != None:
            tags += "[" + mem["fullname"] + "](tg://user?id=" + str(mem["id"]) + ") "

    if len(tags) > 0:
        tags += "А вы почему молчите?"
    logger = get_logger()
    logger.info("tags: %s", tags)
    return tags

def _convert_history(chat_history):
    messages_count = {}
    words_count = {}

    for message in chat_history["messages"]:
        if message["sender"] in messages_count:
            messages_count[message["sender"]] += 1
            words_count[message["sender"]] += _count_words(message["message"])
        else:
            messages_count[message["sender"]] = 1
            words_count[message["sender"]] = _count_words(message["message"])

    return (messages_count, words_count)


def _count_words(s: str):
    return len(re.findall(r'\w+', s.strip()))


def _get_extremum(messages, words):
    minName = maxName = ""
    min = max = 0
    for user, count in messages.items():
        c = words[user] / count
        if max < c:
            max = c
            maxName = user
        if min == 0 or min > c:
            min = c
            minName = user

    return (minName, maxName)