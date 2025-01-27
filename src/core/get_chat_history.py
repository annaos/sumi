import json
import os
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


def get_chat_list():
    directory = f'{HISTORY_SAVE_DIRECTORY}'
    files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
    chats = {}
    for file_name in files:
        path = f'{HISTORY_SAVE_DIRECTORY}/{str(file_name)}'
        with open(path, 'r') as file:
            chat_history = json.load(file)
            if isinstance(chat_history, dict):
                if "title" in chat_history and chat_history["title"] is not None:
                    desc = chat_history["title"]
                elif "messages" in chat_history and len(chat_history["messages"]) > 0:
                    desc = chat_history["messages"][0]["sender"]
                else:
                    desc = ""

                timestamp = chat_history["timestamp"] if "timestamp" in chat_history else chat_history["summary_created_at"] if "summary_created_at" in chat_history else None
                if timestamp is not None:
                    desc += ", "
                    desc += datetime.fromisoformat(timestamp).strftime("%d %B %Y, %H:%M:%S")

                chats[chat_history["chat_id"]] = desc
    return chats
