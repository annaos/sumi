import json
import re
from datetime import datetime, timedelta

from config.common import HISTORY_SAVE_DIRECTORY, CLEAN_FREQUENCY_HOURS

def get_chat_history_by_message_id(chat_id: int, from_message_id: int):
    messages = ""
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)
        timestamp = datetime.fromisoformat(chat_history["last_call"])

        time_diff = datetime.now() - timestamp
        if time_diff < timedelta(hours=CLEAN_FREQUENCY_HOURS):
            return False

        for message in chat_history["messages"]:
            if (message["message_id"] < from_message_id):
                continue

            messages += "%s: %s \n" % (message["sender"], message["message"])

    updateLastCall(chat_history, file_name)
    return messages

def get_chat_history_by_timestamp(chat_id: int, timestamp: str):
    messages_count = {}
    words_count = {}
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)

        for message in chat_history["messages"]:
            if (message["timestamp"] < timestamp):
                continue

            if message["sender"] in messages_count:
                messages_count[message["sender"]] += 1
                words_count[message["sender"]] += count_words(message["message"])
            else:
                messages_count[message["sender"]] = 1
                words_count[message["sender"]] = count_words(message["message"])

    return (messages_count, words_count)

def count_words(s: str):
    return len(re.findall(r'\w+', s.strip()))

def updateLastCall(chat_history, file_name):
    chat_history["last_call"] = datetime.now().isoformat()
    with open(file_name, 'w') as file:
        json.dump(chat_history, file, ensure_ascii=False, indent=2)

