import json
import logging
import os
from datetime import datetime, timedelta

from sumi.config import AI_USAGE_DIRECTORY

logger = logging.getLogger(__name__)


def record_usage(handler, chat_id, in_tokens, out_tokens):
    path = _usage_path(datetime.now())
    usage = _read_json(path)
    usage.append({
        "timestamp": datetime.now().isoformat(),
        "handler": handler,
        "chat_id": chat_id,
        "in_tokens": in_tokens,
        "out_tokens": out_tokens,
    })
    _write_json(path, usage)


def get_usage_report(delta):
    end = datetime.now()
    cutoff = end - delta
    date = cutoff.date()
    totals = {}
    while date <= end.date():
        for entry in _read_json(_usage_path(date)):
            if datetime.fromisoformat(entry["timestamp"]) < cutoff:
                continue
            total = totals.setdefault(entry["handler"], {"in_tokens": 0, "out_tokens": 0, "calls": 0})
            total["in_tokens"] += entry.get("in_tokens", 0)
            total["out_tokens"] += entry.get("out_tokens", 0)
            total["calls"] += 1
        date += timedelta(days=1)
    return totals


def _read_json(path):
    if not os.path.exists(path):
        return []
    try:
        with open(path, 'r') as file:
            return json.load(file)
    except (json.JSONDecodeError, UnicodeDecodeError):
        logger.error("AI usage file %s is broken, starting fresh.", path)
        return []


def _write_json(path, data):
    os.makedirs(AI_USAGE_DIRECTORY, exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, 'w') as file:
        json.dump(data, file, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def _usage_path(date):
    return os.path.join(AI_USAGE_DIRECTORY, "usage_%s.json" % date.strftime("%Y-%m-%d"))
