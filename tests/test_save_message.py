import unittest
from datetime import datetime, timedelta

from src.core.save_message import _replace_message, _clean_history
from src.config.common import CLEAN_LIMIT_DAYS


class ReplaceMessageTestCase(unittest.TestCase):

    def test_replaces_text_of_matching_message(self):
        messages = [
            {"message_id": 1, "message": "old"},
            {"message_id": 2, "message": "other"},
        ]
        updated = _replace_message(messages, {"message_id": 1, "message": "new"})
        self.assertEqual("new", updated[0]["message"])
        self.assertEqual("other", updated[1]["message"])

    def test_unknown_message_id_changes_nothing(self):
        messages = [{"message_id": 1, "message": "old"}]
        updated = _replace_message(messages, {"message_id": 99, "message": "new"})
        self.assertEqual("old", updated[0]["message"])


class CleanHistoryTestCase(unittest.TestCase):

    def _history(self, cleaned_at, message_ages_days):
        return {
            "cleaned_at": cleaned_at,
            "messages": [
                {"message_id": i, "timestamp": (datetime.now() - timedelta(days=days)).isoformat()}
                for i, days in enumerate(message_ages_days)
            ],
        }

    def test_recently_cleaned_history_is_untouched(self):
        old = CLEAN_LIMIT_DAYS + 5
        chat_history = self._history(datetime.now().isoformat(), [old, 1])
        cleaned = _clean_history(chat_history)
        self.assertEqual(2, len(cleaned["messages"]))

    def test_removes_expired_messages_when_cleaning_is_due(self):
        cleaned_at = (datetime.now() - timedelta(days=2)).isoformat()
        chat_history = self._history(cleaned_at, [CLEAN_LIMIT_DAYS + 5, CLEAN_LIMIT_DAYS - 5, 1])
        cleaned = _clean_history(chat_history)
        self.assertEqual([1, 2], [m["message_id"] for m in cleaned["messages"]])

    def test_updates_cleaned_at_timestamp(self):
        cleaned_at = (datetime.now() - timedelta(days=2)).isoformat()
        chat_history = self._history(cleaned_at, [1])
        cleaned = _clean_history(chat_history)
        self.assertGreater(cleaned["cleaned_at"], cleaned_at)


if __name__ == '__main__':
    unittest.main()
