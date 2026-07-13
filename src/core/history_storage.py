import json
import logging
import os
from datetime import datetime, timedelta

from src.config.common import HISTORY_SAVE_DIRECTORY, CLEAN_LIMIT_DAYS, CLEAN_FREQUENCY_HOURS

logger = logging.getLogger(__name__)

META_FILE = "meta.json"
SHARD_PREFIX = "messages_"
SHARD_SUFFIX = ".json"
LEGACY_MIGRATED_SUFFIX = ".migrated"


def load_history(chat_id):
    _migrate_legacy(chat_id)
    directory = _chat_dir(chat_id)
    if not os.path.isdir(directory):
        raise FileNotFoundError(f"No history for chat {chat_id}")
    history = _load_meta(chat_id)
    history["messages"] = []
    for shard in _shard_files(chat_id):
        history["messages"].extend(_read_json_list(os.path.join(directory, shard)))
    return history


def append_message(chat_id, title, message_data):
    _migrate_legacy(chat_id)
    _ensure_meta(chat_id, title)
    path = _shard_path(chat_id, _month(message_data["timestamp"]))
    messages = _read_json_list(path)
    messages.append(message_data)
    _write_json(path, messages)


def update_message(chat_id, message_data):
    _migrate_legacy(chat_id)
    directory = _chat_dir(chat_id)
    for shard in reversed(_shard_files(chat_id)):
        path = os.path.join(directory, shard)
        messages = _read_json_list(path)
        for message in messages:
            if message["message_id"] == message_data["message_id"]:
                message["message"] = message_data["message"]
                _write_json(path, messages)
                return


def update_meta(chat_id, **fields):
    if not os.path.isdir(_chat_dir(chat_id)):
        raise FileNotFoundError(f"No history for chat {chat_id}")
    meta = _load_meta(chat_id)
    meta.update(fields)
    _write_json(_meta_path(chat_id), meta)


def clean_history_if_due(chat_id):
    if not os.path.isdir(_chat_dir(chat_id)):
        return
    meta = _load_meta(chat_id)
    due_limit = (datetime.now() - timedelta(hours=CLEAN_FREQUENCY_HOURS)).isoformat()
    if "cleaned_at" in meta and meta["cleaned_at"] >= due_limit:
        return

    limit = (datetime.now() - timedelta(days=CLEAN_LIMIT_DAYS)).isoformat()
    directory = _chat_dir(chat_id)
    for shard in _shard_files(chat_id):
        path = os.path.join(directory, shard)
        month = _shard_month(shard)
        if month < _month(limit):
            os.remove(path)
        elif month == _month(limit):
            messages = [m for m in _read_json_list(path) if m.get("timestamp") > limit]
            _write_json(path, messages)
    update_meta(chat_id, cleaned_at=datetime.now().isoformat())


def list_chat_ids():
    if not os.path.isdir(HISTORY_SAVE_DIRECTORY):
        return []
    chat_ids = set()
    for entry in os.listdir(HISTORY_SAVE_DIRECTORY):
        try:
            if entry.startswith("chat_history_") and entry.endswith(".json"):
                chat_ids.add(int(entry[len("chat_history_"):-len(".json")]))
            elif entry.startswith("chat_") and os.path.isdir(os.path.join(HISTORY_SAVE_DIRECTORY, entry)):
                chat_ids.add(int(entry[len("chat_"):]))
        except ValueError:
            continue
    return sorted(chat_ids)


def _migrate_legacy(chat_id):
    legacy = os.path.join(HISTORY_SAVE_DIRECTORY, f"chat_history_{str(chat_id)}.json")
    if not os.path.exists(legacy):
        return
    data = _read_json(legacy)
    if not isinstance(data, dict):
        return

    os.makedirs(_chat_dir(chat_id), exist_ok=True)
    messages = data.pop("messages", [])
    _write_json(_meta_path(chat_id), data)

    by_month = {}
    for message in messages:
        by_month.setdefault(_month(message["timestamp"]), []).append(message)
    for month, month_messages in by_month.items():
        _write_json(_shard_path(chat_id, month), month_messages)

    os.replace(legacy, legacy + LEGACY_MIGRATED_SUFFIX)
    logger.info("Migrated legacy history of chat %s into %s", chat_id, _chat_dir(chat_id))


def _ensure_meta(chat_id, title):
    os.makedirs(_chat_dir(chat_id), exist_ok=True)
    if os.path.exists(_meta_path(chat_id)):
        return
    now = datetime.now().isoformat()
    _write_json(_meta_path(chat_id), {
        "chat_id": chat_id,
        "title": title,
        "timestamp": now,
        "summary_created_at": now,
        "cleaned_at": now,
    })


def _load_meta(chat_id):
    meta = None
    if os.path.exists(_meta_path(chat_id)):
        meta = _read_json(_meta_path(chat_id))
    if not isinstance(meta, dict):
        return {"chat_id": chat_id}
    return meta


def _read_json(path):
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        broken = _quarantine(path)
        logger.error("History file %s is broken, moved to %s", path, broken)
        return None


def _read_json_list(path):
    if not os.path.exists(path):
        return []
    data = _read_json(path)
    if isinstance(data, list):
        return data
    if data is not None:
        broken = _quarantine(path)
        logger.error("History file %s has unexpected content, moved to %s", path, broken)
    return []


def _write_json(path, data):
    tmp = path + ".tmp"
    with open(tmp, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _quarantine(path):
    broken = path + ".broken"
    counter = 1
    while os.path.exists(broken):
        broken = "%s.broken%d" % (path, counter)
        counter += 1
    os.replace(path, broken)
    return broken


def _chat_dir(chat_id):
    return os.path.join(HISTORY_SAVE_DIRECTORY, f"chat_{str(chat_id)}")


def _meta_path(chat_id):
    return os.path.join(_chat_dir(chat_id), META_FILE)


def _shard_path(chat_id, month):
    return os.path.join(_chat_dir(chat_id), f"{SHARD_PREFIX}{month}{SHARD_SUFFIX}")


def _shard_files(chat_id):
    directory = _chat_dir(chat_id)
    if not os.path.isdir(directory):
        return []
    return sorted(f for f in os.listdir(directory)
                  if f.startswith(SHARD_PREFIX) and f.endswith(SHARD_SUFFIX))


def _shard_month(file_name):
    return file_name[len(SHARD_PREFIX):-len(SHARD_SUFFIX)]


def _month(timestamp):
    return timestamp[:7]
