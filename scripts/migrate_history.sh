#!/usr/bin/env bash
# Migrate legacy chat_history_<id>.json files into the new sharded format.
#
# Usage (on prod, from anywhere):
#     ./scripts/migrate_history.sh
#
# What it does:
#   1. Backs up saved_data/chats_history/ to saved_data/chats_history_backup_<timestamp>.tar.gz
#   2. Runs `python3 -m src.migrate_history` (idempotent; originals are renamed to *.migrated)
#
# Stop the bot before running so no messages are written during the migration.

set -euo pipefail

cd "$(dirname "$0")/.."

HISTORY_DIR="saved_data/chats_history"

if [ ! -d "$HISTORY_DIR" ]; then
    echo "Nothing to do: $HISTORY_DIR does not exist."
    exit 0
fi

if ! ls "$HISTORY_DIR"/chat_history_*.json >/dev/null 2>&1; then
    echo "Nothing to do: no legacy chat_history_*.json files in $HISTORY_DIR."
    exit 0
fi

echo "Legacy files found:"
ls -lh "$HISTORY_DIR"/chat_history_*.json
echo

read -r -p "Is the bot stopped? Continue with the migration? [y/N] " answer
if [ "$answer" != "y" ] && [ "$answer" != "Y" ]; then
    echo "Aborted, nothing was changed."
    exit 1
fi

BACKUP="saved_data/chats_history_backup_$(date +%Y%m%d-%H%M%S).tar.gz"
tar czf "$BACKUP" -C saved_data chats_history
echo "Backup written to $BACKUP"
echo

python3 -m src.migrate_history

echo
echo "Done. Start the bot again. After checking the result you can delete"
echo "the *.migrated files in $HISTORY_DIR and the backup archive."
