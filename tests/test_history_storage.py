import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import src.core.history_storage as storage
from src.config.common import CLEAN_LIMIT_DAYS

CHAT_ID = -123


def _message(message_id, timestamp, text="msg", sender_id=1, sender="Anna"):
    return {
        "message_id": message_id,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "sender": sender,
        "reply_to": None,
        "message": text,
    }


class StorageTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.history_dir = tmp.name
        patcher = patch("src.core.history_storage.HISTORY_SAVE_DIRECTORY", self.history_dir)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.chat_dir = os.path.join(self.history_dir, "chat_%d" % CHAT_ID)

    def _files(self):
        return sorted(os.listdir(self.chat_dir))


class ShardingTestCase(StorageTestCase):

    def test_append_creates_meta_and_monthly_shard(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-07-13T12:00:00"))
        self.assertEqual(["messages_2026-07.json", "meta.json"], self._files())

    def test_messages_from_different_months_go_to_different_files(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-06-30T23:00:00"))
        storage.append_message(CHAT_ID, "Test Chat", _message(2, "2026-07-01T01:00:00"))
        self.assertIn("messages_2026-06.json", self._files())
        self.assertIn("messages_2026-07.json", self._files())

    def test_load_merges_shards_in_chronological_order(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(2, "2026-07-01T01:00:00"))
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-06-30T23:00:00"))

        history = storage.load_history(CHAT_ID)
        self.assertEqual([1, 2], [m["message_id"] for m in history["messages"]])
        self.assertEqual("Test Chat", history["title"])
        self.assertEqual(CHAT_ID, history["chat_id"])

    def test_load_missing_chat_raises(self):
        with self.assertRaises(FileNotFoundError):
            storage.load_history(999)

    def test_update_message_edits_correct_shard(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-06-30T23:00:00", "старое"))
        storage.append_message(CHAT_ID, "Test Chat", _message(2, "2026-07-01T01:00:00"))

        storage.update_message(CHAT_ID, {"message_id": 1, "message": "новое"})

        history = storage.load_history(CHAT_ID)
        self.assertEqual("новое", history["messages"][0]["message"])
        self.assertEqual(2, len(history["messages"]))

    def test_no_temp_files_left_behind(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-07-13T12:00:00"))
        self.assertFalse([f for f in self._files() if f.endswith(".tmp")])


class BrokenFileTestCase(StorageTestCase):

    def _break_file(self, name):
        with open(os.path.join(self.chat_dir, name), 'w') as file:
            file.write("{broken json")

    def test_broken_shard_is_quarantined_and_others_still_load(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-06-30T23:00:00"))
        storage.append_message(CHAT_ID, "Test Chat", _message(2, "2026-07-01T01:00:00"))
        self._break_file("messages_2026-06.json")

        history = storage.load_history(CHAT_ID)

        self.assertEqual([2], [m["message_id"] for m in history["messages"]])
        self.assertIn("messages_2026-06.json.broken", self._files())

    def test_append_after_broken_shard_starts_fresh_file(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-07-01T01:00:00"))
        self._break_file("messages_2026-07.json")

        storage.append_message(CHAT_ID, "Test Chat", _message(2, "2026-07-02T01:00:00"))

        history = storage.load_history(CHAT_ID)
        self.assertEqual([2], [m["message_id"] for m in history["messages"]])
        self.assertIn("messages_2026-07.json.broken", self._files())

    def test_broken_meta_falls_back_to_chat_id_only(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-07-01T01:00:00"))
        self._break_file("meta.json")

        history = storage.load_history(CHAT_ID)
        self.assertEqual(CHAT_ID, history["chat_id"])
        self.assertEqual([1], [m["message_id"] for m in history["messages"]])

    def test_second_broken_file_gets_numbered_name(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, "2026-07-01T01:00:00"))
        self._break_file("messages_2026-07.json")
        storage.load_history(CHAT_ID)
        self._break_file("messages_2026-07.json")

        storage.load_history(CHAT_ID)
        self.assertIn("messages_2026-07.json.broken1", self._files())


class LegacyMigrationTestCase(StorageTestCase):

    legacy_history = {
        "chat_id": CHAT_ID,
        "title": "Old Chat",
        "timestamp": "2026-06-01T10:00:00",
        "summary_created_at": "2026-07-01T10:00:00",
        "cleaned_at": "2026-07-01T10:00:00",
        "messages": [
            _message(1, "2026-06-15T10:00:00", "june"),
            _message(2, "2026-07-05T10:00:00", "july"),
        ],
    }

    def setUp(self):
        super().setUp()
        self.legacy_path = os.path.join(self.history_dir, "chat_history_%d.json" % CHAT_ID)
        with open(self.legacy_path, 'w') as file:
            json.dump(self.legacy_history, file)

    def test_legacy_file_is_split_into_monthly_shards(self):
        history = storage.load_history(CHAT_ID)

        self.assertEqual(["june", "july"], [m["message"] for m in history["messages"]])
        self.assertEqual("Old Chat", history["title"])
        self.assertIn("messages_2026-06.json", self._files())
        self.assertIn("messages_2026-07.json", self._files())

    def test_legacy_file_is_renamed_after_migration(self):
        storage.load_history(CHAT_ID)
        self.assertFalse(os.path.exists(self.legacy_path))
        self.assertTrue(os.path.exists(self.legacy_path + ".migrated"))

    def test_list_chat_ids_sees_legacy_and_migrated_chats(self):
        self.assertEqual([CHAT_ID], storage.list_chat_ids())
        storage.load_history(CHAT_ID)
        self.assertEqual([CHAT_ID], storage.list_chat_ids())


class CleanHistoryTestCase(StorageTestCase):

    def test_expired_month_shard_is_deleted(self):
        expired = (datetime.now() - timedelta(days=CLEAN_LIMIT_DAYS + 40)).isoformat()
        storage.append_message(CHAT_ID, "Test Chat", _message(1, expired))
        storage.append_message(CHAT_ID, "Test Chat", _message(2, datetime.now().isoformat()))
        storage.update_meta(CHAT_ID, cleaned_at=(datetime.now() - timedelta(days=2)).isoformat())

        storage.clean_history_if_due(CHAT_ID)

        history = storage.load_history(CHAT_ID)
        self.assertEqual([2], [m["message_id"] for m in history["messages"]])
        self.assertNotIn("messages_%s.json" % expired[:7], self._files())

    def test_recently_cleaned_chat_is_untouched(self):
        expired = (datetime.now() - timedelta(days=CLEAN_LIMIT_DAYS + 40)).isoformat()
        storage.append_message(CHAT_ID, "Test Chat", _message(1, expired))

        storage.clean_history_if_due(CHAT_ID)

        history = storage.load_history(CHAT_ID)
        self.assertEqual([1], [m["message_id"] for m in history["messages"]])

    def test_cleaning_updates_cleaned_at(self):
        storage.append_message(CHAT_ID, "Test Chat", _message(1, datetime.now().isoformat()))
        old_cleaned_at = (datetime.now() - timedelta(days=2)).isoformat()
        storage.update_meta(CHAT_ID, cleaned_at=old_cleaned_at)

        storage.clean_history_if_due(CHAT_ID)

        self.assertGreater(storage.load_history(CHAT_ID)["cleaned_at"], old_cleaned_at)


if __name__ == '__main__':
    unittest.main()
