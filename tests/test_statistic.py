import unittest
from datetime import timedelta

from sumi.statistic import (
    create_statistic,
    _convert_history,
    _count_words,
    _get_extremum,
    _is_wordle,
    _count_wordle,
    _count_green,
    _count_yellow,
)


def _message(sender_id, sender, text):
    return {"sender_id": sender_id, "sender": sender, "message": text}


class ConvertHistoryTestCase(unittest.TestCase):

    def test_counts_messages_and_words_per_sender(self):
        chat_history = {"messages": [
            _message(1, "Anna", "привет всем"),
            _message(2, "Sven", "привет"),
            _message(1, "Anna", "как дела сегодня"),
        ]}
        converted = _convert_history(chat_history)
        self.assertEqual({"sender": "Anna", "count": 2, "words": 5}, converted[1])
        self.assertEqual({"sender": "Sven", "count": 1, "words": 1}, converted[2])


class CreateStatisticTestCase(unittest.TestCase):

    def test_empty_history(self):
        statistic = create_statistic({"chat_id": -123, "messages": []}, timedelta(hours=10))
        self.assertIn("Никто ничего не написал", statistic)

    def test_header_with_delta(self):
        statistic = create_statistic({"chat_id": -123, "messages": []}, timedelta(hours=10))
        self.assertIn("Статистика за последние", statistic)

    def test_header_without_delta(self):
        statistic = create_statistic({"chat_id": -123, "messages": []}, None)
        self.assertIn("Статистика после указанного сообщения", statistic)

    def test_ranks_senders_by_message_count(self):
        chat_history = {"chat_id": -123, "messages": [
            _message(1, "Anna", "раз два"),
            _message(1, "Anna", "три"),
            _message(2, "Sven", "один"),
        ]}
        statistic = create_statistic(chat_history, timedelta(hours=10))
        self.assertIn("\U0001F947", statistic)
        self.assertLess(statistic.index("Anna"), statistic.index("Sven"))
        self.assertIn("Anna: 2 сообщений", statistic)
        self.assertIn("Sven: 1 сообщение", statistic)

    def test_escapes_markdown_special_chars(self):
        chat_history = {"chat_id": -123, "messages": [
            _message(1, "Anna", "привет!"),
        ]}
        statistic = create_statistic(chat_history, timedelta(hours=10))
        self.assertNotIn(".", statistic.replace("\\.", ""))


class WordCountTestCase(unittest.TestCase):

    def test_count_words(self):
        self.assertEqual(3, _count_words("привет  всем друзья"))
        self.assertEqual(0, _count_words("   "))

    def test_get_extremum(self):
        messages = {
            1: {"sender": "Anna", "count": 1, "words": 10},
            2: {"sender": "Sven", "count": 2, "words": 2},
            3: {"sender": "Mia", "count": 1, "words": 5},
        }
        self.assertEqual(("Sven", "Anna"), _get_extremum(messages))


class WordleTestCase(unittest.TestCase):

    wordle_message = "Вордли дня #742 4/6\n🟩🟨⬜⬜⬜\n🟩🟩🟩🟩🟩"

    def test_is_wordle(self):
        self.assertTrue(_is_wordle(self.wordle_message))
        self.assertFalse(_is_wordle("просто сообщение"))

    def test_count_wordle_attempts(self):
        self.assertEqual(4, _count_wordle(self.wordle_message))

    def test_count_wordle_no_result_counts_as_eight(self):
        self.assertEqual(8, _count_wordle("Вордли дня #742 X/6"))

    def test_count_colors(self):
        self.assertEqual(6, _count_green(self.wordle_message))
        self.assertEqual(1, _count_yellow(self.wordle_message))


if __name__ == '__main__':
    unittest.main()
