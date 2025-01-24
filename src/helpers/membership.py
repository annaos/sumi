from datetime import datetime
import os
import json
from config.common import HISTORY_MEMBERS_DIRECTORY
from telegram import User


def add_entry(chat_id, user: User, join: bool):
    data = {
        "id": user.id,
        "username": user.username,
        "fullname": user.full_name,
        "status": "join" if join else "leave",
        "timestamp": datetime.now().isoformat(),
    }
    history = _read_history_json(chat_id)
    if len(history) > 100:
        _archive_history_json(chat_id, history)
        history = []
    history.append(data)
    _write_history_json(chat_id, history)


def get_last_entries(chat_id, count: int):
    return _read_history_json(chat_id)[-count:]


def _get_file_name(chat_id):
    filename = f'{HISTORY_MEMBERS_DIRECTORY}/history_{str(chat_id)}.json'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename


def _archive_history_json(chat_id, history):
    archived_filename = f'{HISTORY_MEMBERS_DIRECTORY}/history_{str(chat_id)}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
    with open(archived_filename, 'w') as file:
        json.dump(history, file, ensure_ascii=False, indent=2)


#TODO check archived version
def _read_history_json(chat_id):
    try:
        with open(_get_file_name(chat_id), 'r') as file:
            members_history = json.load(file)
    except FileNotFoundError:
        members_history = []

    return members_history


def _write_history_json(chat_id, history):
    with open(_get_file_name(chat_id), 'w') as file:
        json.dump(history, file, ensure_ascii=False, indent=2)