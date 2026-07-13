import copy
import unittest
from unittest.mock import patch, Mock

from src.history.read import (
    get_chat_history_by_message_id,
    get_chat_history_by_timestamp,
    get_chat_history_by_user_id,
    get_message_history_by_message,
)


def _message(message_id, timestamp, sender_id, sender, text, reply_to=None):
    return {
        "message_id": message_id,
        "timestamp": timestamp,
        "sender_id": sender_id,
        "sender": sender,
        "reply_to": reply_to,
        "message": text,
    }


SAMPLE_HISTORY = {
    "chat_id": -123,
    "summary_created_at": "2026-07-12T23:50:47.117097",
    "cleaned_at": "2026-07-12T20:50:58.147062",
    "messages": [
        _message(10, "2026-07-10T14:24:55.493818", 1, "Anna Os", "First"),
        _message(11, "2026-07-11T14:24:55.493818", 2, "Sven", "Second", reply_to=10),
        _message(16, "2026-07-12T14:24:55.493818", 1, "Anna Os", "Third", reply_to=11),
    ],
}


def _patch_storage():
    return patch("src.history.read.storage.load_history",
                 side_effect=lambda chat_id: copy.deepcopy(SAMPLE_HISTORY))


class GetChatHistoryTestCase(unittest.TestCase):

    def test_by_message_id(self):
        with _patch_storage():
            history = get_chat_history_by_message_id(-123, 11)
        self.assertEqual([11, 16], [m["message_id"] for m in history["messages"]])

    def test_by_message_id_keeps_metadata(self):
        with _patch_storage():
            history = get_chat_history_by_message_id(-123, 11)
        self.assertEqual(-123, history["chat_id"])
        self.assertEqual(SAMPLE_HISTORY["summary_created_at"], history["summary_created_at"])

    def test_by_timestamp(self):
        with _patch_storage():
            history = get_chat_history_by_timestamp(-123, "2026-07-11T00:00:00")
        self.assertEqual([11, 16], [m["message_id"] for m in history["messages"]])

    def test_by_timestamp_nothing_matches(self):
        with _patch_storage():
            history = get_chat_history_by_timestamp(-123, "2026-07-13T00:00:00")
        self.assertEqual([], history["messages"])

    def test_by_user_id(self):
        with _patch_storage():
            history = get_chat_history_by_user_id(-123, 1, "2026-07-01T00:00:00")
        self.assertEqual([10, 16], [m["message_id"] for m in history["messages"]])

    def test_by_user_id_respects_timestamp(self):
        with _patch_storage():
            history = get_chat_history_by_user_id(-123, 1, "2026-07-11T00:00:00")
        self.assertEqual([16], [m["message_id"] for m in history["messages"]])


class GetMessageHistoryByMessageTestCase(unittest.TestCase):

    def test_follows_reply_chain(self):
        message = Mock(chat_id=-123, message_id=16)
        with _patch_storage():
            history = get_message_history_by_message(message)
        self.assertEqual(["First", "Second", "Third"], [m["message"] for m in history])

    def test_unknown_message_falls_back_to_message_itself(self):
        message = Mock(chat_id=-123, message_id=99, text="Fresh", caption=None)
        message.from_user.full_name = "Anna Os"
        with _patch_storage():
            history = get_message_history_by_message(message)
        self.assertEqual([{"sender": "Anna Os", "message": "Fresh"}], history)


if __name__ == '__main__':
    unittest.main()
