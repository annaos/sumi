import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

from telegram import Chat, Message, User

import src.history.storage as storage
from src.history.save import save_message, save_private_sender, get_private_sender_id
from src.history.read import (
    get_chat_history_by_message_id,
    get_chat_history_by_timestamp,
    get_chat_history_by_user_id,
    get_message_history_by_message,
    get_chat_list,
    updateLastCall,
)
from src.statistic import create_statistic

CHAT_ID = -123


def _tg_message(message_id, text, sender_id=1, sender_name="Anna", reply_to=None):
    return Message(
        message_id=message_id,
        date=datetime.now(),
        chat=Chat(id=CHAT_ID, type=Chat.GROUP, title="Test Chat"),
        from_user=User(id=sender_id, first_name=sender_name, is_bot=False),
        text=text,
        reply_to_message=reply_to,
    )


class HistoryDirectoryTestCase(unittest.TestCase):
    """Base: redirect the history directory to a temp dir, real files inside."""

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.history_dir = tmp.name
        for target in ("src.history.save.HISTORY_SAVE_DIRECTORY",
                       "src.history.storage.HISTORY_SAVE_DIRECTORY"):
            patcher = patch(target, self.history_dir)
            patcher.start()
            self.addCleanup(patcher.stop)
        env = patch.dict(os.environ, {"ACTIVE_CHAT_IDS": "-999", "ACTIVE_MEMBERSHIP_CHAT_IDS": "-999"})
        env.start()
        self.addCleanup(env.stop)


class SaveAndReadRoundTripTestCase(HistoryDirectoryTestCase):

    def test_saved_messages_can_be_read_back(self):
        save_message(_tg_message(1, "Первое"), is_edited=False)
        save_message(_tg_message(2, "Второе", sender_id=2, sender_name="Sven"), is_edited=False)

        history = get_chat_history_by_message_id(CHAT_ID, 1)

        self.assertEqual(CHAT_ID, history["chat_id"])
        self.assertEqual("Test Chat", history["title"])
        self.assertEqual(["Первое", "Второе"], [m["message"] for m in history["messages"]])
        self.assertEqual(["Anna", "Sven"], [m["sender"] for m in history["messages"]])

    def test_filter_by_message_id_skips_earlier_messages(self):
        for message_id in [1, 2, 3]:
            save_message(_tg_message(message_id, "msg %d" % message_id), is_edited=False)

        history = get_chat_history_by_message_id(CHAT_ID, 2)
        self.assertEqual([2, 3], [m["message_id"] for m in history["messages"]])

    def test_filter_by_timestamp_returns_recent_messages(self):
        save_message(_tg_message(1, "old"), is_edited=False)
        cutoff = datetime.now().isoformat()
        save_message(_tg_message(2, "new"), is_edited=False)

        history = get_chat_history_by_timestamp(CHAT_ID, cutoff)
        self.assertEqual(["new"], [m["message"] for m in history["messages"]])

    def test_filter_by_user_id(self):
        save_message(_tg_message(1, "от Анны", sender_id=1), is_edited=False)
        save_message(_tg_message(2, "от Свена", sender_id=2, sender_name="Sven"), is_edited=False)
        save_message(_tg_message(3, "снова Анна", sender_id=1), is_edited=False)

        long_ago = (datetime.now() - timedelta(days=1)).isoformat()
        history = get_chat_history_by_user_id(CHAT_ID, 1, long_ago)
        self.assertEqual([1, 3], [m["message_id"] for m in history["messages"]])

    def test_edited_message_replaces_original_text(self):
        save_message(_tg_message(1, "опечтка"), is_edited=False)
        save_message(_tg_message(1, "опечатка"), is_edited=True)

        history = get_chat_history_by_message_id(CHAT_ID, 1)
        self.assertEqual(1, len(history["messages"]))
        self.assertEqual("опечатка", history["messages"][0]["message"])

    def test_reply_chain_round_trip(self):
        first = _tg_message(1, "Вопрос")
        second = _tg_message(2, "Ответ", sender_id=2, sender_name="Sven", reply_to=first)
        third = _tg_message(3, "Уточнение", reply_to=second)
        for message in [first, second, third]:
            save_message(message, is_edited=False)

        chain = get_message_history_by_message(third)
        self.assertEqual(["Вопрос", "Ответ", "Уточнение"], [m["message"] for m in chain])

    def test_message_without_saved_history_falls_back_to_itself(self):
        save_message(_tg_message(1, "что-то"), is_edited=False)

        unsaved = _tg_message(99, "новое сообщение")
        chain = get_message_history_by_message(unsaved)
        self.assertEqual([{"sender": "Anna", "message": "новое сообщение"}], chain)


class ChatMetadataTestCase(HistoryDirectoryTestCase):

    def test_update_last_call_bumps_summary_timestamp(self):
        save_message(_tg_message(1, "msg"), is_edited=False)
        before = get_chat_history_by_message_id(CHAT_ID, 1)["summary_created_at"]

        updateLastCall(CHAT_ID)

        after = get_chat_history_by_message_id(CHAT_ID, 1)["summary_created_at"]
        self.assertGreater(after, before)

    def test_get_chat_list_shows_saved_chat_with_title(self):
        save_message(_tg_message(1, "msg"), is_edited=False)

        chats = get_chat_list()
        self.assertIn(CHAT_ID, chats)
        self.assertIn("Test Chat", chats[CHAT_ID])


class StatisticFromSavedHistoryTestCase(HistoryDirectoryTestCase):

    def test_statistic_over_saved_messages(self):
        save_message(_tg_message(1, "раз два три", sender_id=1), is_edited=False)
        save_message(_tg_message(2, "четыре", sender_id=1), is_edited=False)
        save_message(_tg_message(3, "пять", sender_id=2, sender_name="Sven"), is_edited=False)

        history = get_chat_history_by_message_id(CHAT_ID, 1)
        statistic = create_statistic(history, timedelta(hours=10))

        self.assertIn("Anna: 2 сообщений", statistic)
        self.assertIn("Sven: 1 сообщение", statistic)
        self.assertLess(statistic.index("Anna"), statistic.index("Sven"))


class ShardedStorageTestCase(HistoryDirectoryTestCase):

    def _chat_dir(self):
        return os.path.join(self.history_dir, "chat_%d" % CHAT_ID)

    def test_saved_messages_land_in_monthly_shard_files(self):
        save_message(_tg_message(1, "сегодня"), is_edited=False)
        last_month = (datetime.now() - timedelta(days=40)).isoformat()
        storage.append_message(CHAT_ID, "Test Chat", {
            "message_id": 0, "timestamp": last_month, "sender_id": 1,
            "sender": "Anna", "reply_to": None, "message": "давно",
        })

        shards = [f for f in os.listdir(self._chat_dir()) if f.startswith("messages_")]
        self.assertEqual(2, len(shards))

        history = get_chat_history_by_message_id(CHAT_ID, 0)
        self.assertEqual(["давно", "сегодня"], [m["message"] for m in history["messages"]])

    def test_broken_shard_is_quarantined_and_history_survives(self):
        save_message(_tg_message(1, "будет потеряно"), is_edited=False)
        current_shard = "messages_%s.json" % datetime.now().isoformat()[:7]
        with open(os.path.join(self._chat_dir(), current_shard), 'w') as file:
            file.write("{broken json")

        save_message(_tg_message(2, "новое"), is_edited=False)

        history = get_chat_history_by_message_id(CHAT_ID, 0)
        self.assertEqual(["новое"], [m["message"] for m in history["messages"]])
        self.assertIn(current_shard + ".broken", os.listdir(self._chat_dir()))

    def test_legacy_single_file_history_is_migrated_on_read(self):
        legacy_path = os.path.join(self.history_dir, "chat_history_%d.json" % CHAT_ID)
        with open(legacy_path, 'w') as file:
            json.dump({
                "chat_id": CHAT_ID,
                "title": "Old Chat",
                "timestamp": "2026-06-01T10:00:00",
                "summary_created_at": "2026-06-01T10:00:00",
                "cleaned_at": "2026-06-01T10:00:00",
                "messages": [{
                    "message_id": 1, "timestamp": "2026-06-15T10:00:00", "sender_id": 1,
                    "sender": "Anna", "reply_to": None, "message": "старое сообщение",
                }],
            }, file)

        history = get_chat_history_by_message_id(CHAT_ID, 0)

        self.assertEqual(["старое сообщение"], [m["message"] for m in history["messages"]])
        self.assertEqual("Old Chat", history["title"])
        self.assertFalse(os.path.exists(legacy_path))
        self.assertTrue(os.path.exists(legacy_path + ".migrated"))

        save_message(_tg_message(2, "новое сообщение"), is_edited=False)
        history = get_chat_history_by_message_id(CHAT_ID, 0)
        self.assertEqual(2, len(history["messages"]))


class PrivateSenderRoundTripTestCase(HistoryDirectoryTestCase):

    def test_saved_sender_found_by_username_and_full_name(self):
        save_private_sender(111, "Anna Os", "anna_os")

        self.assertEqual(111, get_private_sender_id("anna_os"))
        self.assertEqual(111, get_private_sender_id("Anna Os"))

    def test_unknown_sender_returns_none(self):
        save_private_sender(111, "Anna Os", "anna_os")
        self.assertIsNone(get_private_sender_id("somebody_else"))

    def test_saving_same_chat_twice_keeps_one_entry(self):
        save_private_sender(111, "Anna Os", "anna_os")
        save_private_sender(111, "Anna Os", "anna_os")

        self.assertEqual(111, get_private_sender_id("anna_os"))


if __name__ == '__main__':
    unittest.main()
