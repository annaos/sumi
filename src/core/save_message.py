import json
import os
from telegram import Message
from datetime import datetime
from src.config.common import HISTORY_SAVE_DIRECTORY
from src.helpers.util import is_active_chat, get_logger
import src.helpers.member as member
import src.core.history_storage as storage

def save_message(message: Message, is_edited: bool):
    chat_id = message.chat_id
    message_text = message.text if message.text else message.caption

    message_data = {
        "message_id": message.message_id,
        "timestamp": datetime.now().isoformat(),
        "sender_id": message.from_user.id,
        "sender": message.from_user.full_name,
        "reply_to": message.reply_to_message.message_id if message.reply_to_message is not None else None,
        "message": message_text
    }

    if is_edited:
        storage.update_message(chat_id, message_data)
    else:
        storage.append_message(chat_id, message.chat.title, message_data)

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

