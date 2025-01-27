import json
import os
from telegram import Message
from datetime import timedelta, datetime
from config.common import HISTORY_SAVE_DIRECTORY, CLEAN_LIMIT_DAYS, CLEAN_FREQUENCY_HOURS
from helpers.util import is_active_chat, get_logger
import helpers.member as member

def save_message(message: Message, is_edited: bool):
    chat_id = message.chat_id
    message_id = message.message_id
    sender = message.from_user.full_name
    message_text = message.text if message.text else message.caption

    file_name = f'{HISTORY_SAVE_DIRECTORY}/chat_history_{str(chat_id)}.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    message_data = {
        "message_id": message_id,
        "timestamp": datetime.now().isoformat(),
        "sender_id": message.from_user.id,
        "sender": sender,
        "reply_to": message.reply_to_message.message_id if message.reply_to_message is not None else None,
        "message": message_text
    }

    try:
        with open(file_name, 'r') as file:
            chat_history = json.load(file)

    except FileNotFoundError:
        chat_history = {
            "chat_id": chat_id,
            "title": message.chat.title,
            "timestamp": datetime.now().isoformat(),
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
        member.update_member(chat_id, message.from_user)


def save_private_sender(chat_id, full_name, username):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/private_chats.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    try:
        with open(file_name, 'r') as file:
            chat_history = json.load(file)
            if any(chat["chat_id"] == chat_id for chat in chat_history):
                return
    except FileNotFoundError:
        chat_history = []

    chat_history.append({
        "username": username,
        "chat_id": chat_id,
        "full_name": full_name,
    })
    with open(file_name, 'w') as file:
        json.dump(chat_history, file, ensure_ascii=False, indent=2)


def get_private_sender_id(name):
    file_name = f'{HISTORY_SAVE_DIRECTORY}/private_chats.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)
    try:
        with open(file_name, 'r') as file:
            chat_history = json.load(file)
            for chat in chat_history:
                if chat["username"] == name or chat["full_name"] == name:
                    return chat["chat_id"]
    except Exception as e:
        logger = get_logger()
        logger.error("An error occurred: %s", e)
    return None


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

