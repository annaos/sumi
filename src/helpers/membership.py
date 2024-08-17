from datetime import datetime
import os
import json
from config.common import HISTORY_MEMBERS_DIRECTORY
from telegram import User


def get_all_members(chat_id):
    members = _read_members_json(chat_id)
    active_members = [v for v in members if "left_at" not in v]

    return active_members


def add_member(chat_id, user: User):
    member_data = {
        "id": user.id,
        "username": user.username,
        "fullname": user.full_name,
        "join_at": datetime.now().isoformat(),
    }
    members = _read_members_json(chat_id)
    members.append(member_data)
    _write_members_json(chat_id, members)


def update_member(chat_id, user: User):
    member_data = {
        "id": user.id,
        "username": user.username,
        "fullname": user.full_name,
        "join_at": None,
    }

    members = _read_members_json(chat_id)
    for i, member in enumerate(members):
        if member["fullname"] == user.full_name and member["id"] == None:
            members[i] = member_data
            _write_members_json(chat_id, members)
            return

    members.append(member_data)
    _write_members_json(chat_id, members)


def left_member(chat_id, user: User):
    members = _read_members_json(chat_id)
    for i in range(len(members)):
        if members[i]["fullname"] == user.full_name and "left_at" not in members[i]:
            members[i]["left_at"] = datetime.now().isoformat()
            break

    _write_members_json(chat_id, members)


def _get_file_name(chat_id):
    filename = f'{HISTORY_MEMBERS_DIRECTORY}/members_{str(chat_id)}.json'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename


def _read_members_json(chat_id):
    try:
        with open(_get_file_name(chat_id), 'r') as file:
            members_history = json.load(file)
    except FileNotFoundError:
        members_history = []

    return members_history


def _write_members_json(chat_id, members):
    with open(_get_file_name(chat_id), 'w') as file:
        json.dump(members, file, ensure_ascii=False, indent=2)