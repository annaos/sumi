import json
import os
from telegram import Message
from datetime import timedelta, datetime
from config.common import HISTORY_SAVE_DIRECTORY, CLEAN_LIMIT_DAYS, CLEAN_FREQUENCY_HOURS
from helpers.util import is_active_chat
import helpers.membership as membership

def save_message(message: Message, is_edited: bool):
    chat_id = message.chat_id
    message_id = message.message_id
    sender = message.from_user.full_name
    message_text = message.text

    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    message_data = {
        "message_id": message_id,
        "timestamp": datetime.now().isoformat(),
        "sender_id": message.from_user.id,
        "sender": sender,
        "message": message_text
    }

    try:
        with open(file_name, 'r') as file:
            chat_history = json.load(file)

    except FileNotFoundError:
        chat_history = {
            "chat_id": chat_id,
            "title": message.chat.title,
            "summary_created_at": datetime.now().isoformat(),
            "cleaned_at": datetime.now().isoformat(),
            "messages": []
        }

    if is_edited:
        chat_history["messages"] = _replace_message(chat_history["messages"], message_data)
    else:
        chat_history["messages"].append(message_data)

    chat_history = _clean_history(chat_history)
    with open(file_name, 'w') as file:
        json.dump(chat_history, file, ensure_ascii=False, indent=2)

    if is_active_chat(chat_id):
        membership.update_member(chat_id, message.from_user)


def _replace_message(messages, updated_message):
    for i in range(len(messages)):
        if messages[i]["message_id"] == updated_message["message_id"]:
            messages[i] = updated_message
            break
    return messages


def _clean_history(chat_history):
    cleaned_limit = (datetime.now() - timedelta(hours=CLEAN_FREQUENCY_HOURS)).isoformat()
    if not "cleaned_at" in chat_history or chat_history["cleaned_at"] < cleaned_limit:
        messages = chat_history["messages"]
        limit = (datetime.now() - timedelta(days=CLEAN_LIMIT_DAYS)).isoformat()

        messages[:] = [d for d in messages if d.get('timestamp') > limit]

        chat_history["cleaned_at"] = datetime.now().isoformat()
    return chat_history

