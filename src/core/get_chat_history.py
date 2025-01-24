import json
from datetime import datetime

from config.common import HISTORY_SAVE_DIRECTORY, SUMMARY_HOURS_LIMIT

def get_chat_history_by_message_id(chat_id: int, from_message_id: int):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)
        chat_history["messages"] = [x for x in chat_history["messages"] if x["message_id"] >= from_message_id]
    return chat_history


def get_chat_history_by_timestamp(chat_id: int, timestamp: str):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)
        chat_history["messages"] = [x for x in chat_history["messages"] if x["timestamp"] >= timestamp]
    return chat_history


def get_chat_history_by_user_id(chat_id: int, user_id: int, timestamp: str):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)
        chat_history["messages"] = [x for x in chat_history["messages"] if x["timestamp"] >= timestamp and x["sender_id"] == user_id]
    return chat_history


def updateLastCall(chat_id):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'

    with open(file_name, 'r') as file:
        chat_history = json.load(file)

    chat_history["summary_created_at"] = datetime.now().isoformat()
    with open(file_name, 'w') as file:
        json.dump(chat_history, file, ensure_ascii=False, indent=2)

