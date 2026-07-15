import json
import os

from telegram import User

from sumi.config import JOKE_TARGETS_DIRECTORY


def add_target(chat_id, user: User):
    targets = _read_targets_json(chat_id)
    for existing in targets:
        if existing["id"] == user.id:
            return

    targets.append({
        "id": user.id,
        "username": user.username,
        "fullname": user.full_name,
    })
    _write_targets_json(chat_id, targets)


def remove_target(chat_id, user_id):
    targets = _read_targets_json(chat_id)
    remaining = [target for target in targets if target["id"] != user_id]
    if len(remaining) != len(targets):
        _write_targets_json(chat_id, remaining)


def is_target(chat_id, user_id) -> bool:
    return any(target["id"] == user_id for target in _read_targets_json(chat_id))


def _get_file_name(chat_id):
    filename = f'{JOKE_TARGETS_DIRECTORY}/targets_{str(chat_id)}.json'
    os.makedirs(os.path.dirname(filename), exist_ok=True)
    return filename


def _read_targets_json(chat_id):
    try:
        with open(_get_file_name(chat_id), 'r') as file:
            return json.load(file)
    except FileNotFoundError:
        return []


def _write_targets_json(chat_id, targets):
    with open(_get_file_name(chat_id), 'w') as file:
        json.dump(targets, file, ensure_ascii=False, indent=2)
