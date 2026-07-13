"""One-shot migration of legacy chat_history_<id>.json files into the sharded format.

Usage (from the repo root):
    python -m src.migrate_history

Safe to run repeatedly: each legacy file is converted into saved_data/chats_history/
chat_<id>/ (meta.json + monthly messages_YYYY-MM.json shards) and the original is
renamed to *.migrated. Unreadable files are quarantined as *.broken. Files that do
not match the chat_history_<id>.json pattern are reported and left untouched.
"""
import os

from src.config import HISTORY_SAVE_DIRECTORY
import src.history.storage as storage

LEGACY_PREFIX = "chat_history_"
LEGACY_SUFFIX = ".json"


def find_legacy_files():
    legacy = []
    skipped = []
    for entry in sorted(os.listdir(HISTORY_SAVE_DIRECTORY)):
        if not entry.startswith(LEGACY_PREFIX) or not entry.endswith(LEGACY_SUFFIX):
            continue
        try:
            chat_id = int(entry[len(LEGACY_PREFIX):-len(LEGACY_SUFFIX)])
        except ValueError:
            skipped.append(entry)
            continue
        legacy.append((chat_id, entry))
    return legacy, skipped


def migrate_all():
    print(f"History directory: {HISTORY_SAVE_DIRECTORY}")
    legacy, skipped = find_legacy_files()

    if not legacy:
        print("No legacy history files found — nothing to migrate.")
    for chat_id, file_name in legacy:
        size_kb = os.path.getsize(os.path.join(HISTORY_SAVE_DIRECTORY, file_name)) / 1024
        try:
            history = storage.load_history(chat_id)
        except FileNotFoundError:
            print(f"BROKEN   {file_name} ({size_kb:.0f} KB): unreadable, quarantined as *.broken")
            continue
        chat_dir = storage._chat_dir(chat_id)
        shards = [f for f in os.listdir(chat_dir) if f.startswith(storage.SHARD_PREFIX)]
        print(f"MIGRATED {file_name} ({size_kb:.0f} KB): "
              f"{len(history['messages'])} messages -> {os.path.basename(chat_dir)}/ ({len(shards)} monthly files)")

    for entry in skipped:
        print(f"SKIPPED  {entry}: name does not match {LEGACY_PREFIX}<id>{LEGACY_SUFFIX}, left untouched")

    if legacy:
        print("\nOriginals were renamed to *.migrated — delete them after checking the result.")


if __name__ == '__main__':
    migrate_all()
