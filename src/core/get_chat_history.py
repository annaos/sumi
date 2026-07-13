from datetime import datetime

from telegram import Message

import src.core.history_storage as storage

def get_chat_history_by_message_id(chat_id: int, from_message_id: int):
    chat_history = storage.load_history(chat_id)
    chat_history["messages"] = [x for x in chat_history["messages"] if x["message_id"] >= from_message_id]
    return chat_history

def get_message_history_by_message(mes: Message):
    message_history = []
    chat_history = storage.load_history(mes.chat_id)
    rep_m = _get_reply_to_message(chat_history, mes.message_id)
    if rep_m is None:
        return [{"sender": mes.from_user.full_name, "message": mes.text if mes.text else mes.caption}]
    message_history.insert(0, rep_m)
    while rep_m and rep_m["reply_to"]:
        rep_m = _get_reply_to_message(chat_history, rep_m["reply_to"])
        message_history.insert(0, rep_m)

    return message_history


def _get_reply_to_message(chat_history, message_id):
    return next((x for x in chat_history["messages"] if x["message_id"] == message_id), None)


def get_chat_history_by_timestamp(chat_id: int, timestamp: str):
    chat_history = storage.load_history(chat_id)
    chat_history["messages"] = [x for x in chat_history["messages"] if x["timestamp"] >= timestamp]
    return chat_history


def get_chat_history_by_user_id(chat_id: int, user_id: int, timestamp: str):
    chat_history = storage.load_history(chat_id)
    chat_history["messages"] = [x for x in chat_history["messages"] if x["timestamp"] >= timestamp and x["sender_id"] == user_id]
    return chat_history


def updateLastCall(chat_id):
    storage.update_meta(chat_id, summary_created_at=datetime.now().isoformat())


def get_chat_list():
    chats = {}
    for chat_id in storage.list_chat_ids():
        try:
            chat_history = storage.load_history(chat_id)
        except FileNotFoundError:
            continue

        if "title" in chat_history and chat_history["title"] is not None:
            desc = chat_history["title"]
        elif len(chat_history["messages"]) > 0:
            desc = chat_history["messages"][0]["sender"]
        else:
            desc = ""

        timestamp = chat_history["timestamp"] if "timestamp" in chat_history else chat_history.get("summary_created_at")
        if timestamp is not None:
            desc += ", "
            desc += datetime.fromisoformat(timestamp).strftime("%d %B %Y, %H:%M:%S")

        chats[chat_history["chat_id"]] = desc
    return chats
