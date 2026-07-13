import unittest
from unittest.mock import Mock
from datetime import datetime, timedelta

from src.utils import (
    get_boundary,
    get_point,
    get_poll_options,
    get_statistic_boundary,
    get_time_delta,
    _divide_args,
)
from src.config import STATISTIC_HOURS


class GetBoundaryTestCase(unittest.TestCase):

    def test_hours(self):
        for hours in [2, 4, 16]:
            with self.subTest(hours=hours):
                self.assertEqual(timedelta(hours=hours), get_boundary(['%dh' % hours]))

    def test_minutes(self):
        for minutes in [2, 30, 90]:
            with self.subTest(minutes=minutes):
                self.assertEqual(timedelta(minutes=minutes), get_boundary(['%dm' % minutes]))

    def test_days(self):
        self.assertEqual(timedelta(days=7), get_boundary(['7d']))

    def test_time_after_point(self):
        self.assertEqual(timedelta(hours=3), get_boundary(['погода', '3h']))

    def test_invalid_falls_back_to_default(self):
        self.assertEqual(timedelta(hours=STATISTIC_HOURS), get_boundary(['bla']))

    def test_empty_falls_back_to_default(self):
        self.assertEqual(timedelta(hours=STATISTIC_HOURS), get_boundary([]))

    def test_custom_default(self):
        default = timedelta(days=1)
        self.assertEqual(default, get_boundary([], default))


class DivideArgsTestCase(unittest.TestCase):

    def test_time_then_point(self):
        self.assertEqual(('2h', 'погода в берлине'), _divide_args(['2h', 'погода', 'в', 'берлине']))

    def test_point_then_time(self):
        self.assertEqual(('2h', 'погода'), _divide_args(['погода', '2h']))

    def test_only_time(self):
        self.assertEqual(('30m', ''), _divide_args(['30m']))

    def test_only_point(self):
        self.assertEqual(('', 'погода'), _divide_args(['погода']))

    def test_empty(self):
        self.assertEqual(('', ''), _divide_args([]))


class GetPointTestCase(unittest.TestCase):

    def test_point_after_time(self):
        self.assertEqual('погода', get_point(['2h', 'погода']))

    def test_point_only(self):
        self.assertEqual('погода в берлине', get_point(['погода', 'в', 'берлине']))

    def test_no_point(self):
        self.assertEqual('', get_point(['2h']))


class GetPollOptionsTestCase(unittest.TestCase):

    def test_quoted_options(self):
        self.assertEqual(['Да', 'Нет, никогда'], get_poll_options('"Да" "Нет, никогда"'))

    def test_ignores_blank_parts(self):
        self.assertEqual(['a', 'b'], get_poll_options('  "a"   "b"  '))

    def test_empty(self):
        self.assertEqual([], get_poll_options(''))


class GetStatisticBoundaryTestCase(unittest.TestCase):

    def test_reply_to_regular_message(self):
        reply = Mock(message_id=42, message_thread_id=1)
        self.assertEqual((42, None), get_statistic_boundary(reply, []))

    def test_reply_to_thread_root_uses_args(self):
        reply = Mock(message_id=42, message_thread_id=42)
        self.assertEqual((None, timedelta(hours=2)), get_statistic_boundary(reply, ['2h']))

    def test_no_reply_uses_args(self):
        self.assertEqual((None, timedelta(hours=2)), get_statistic_boundary(None, ['2h']))

    def test_no_reply_no_args_uses_default(self):
        self.assertEqual((None, timedelta(hours=STATISTIC_HOURS)), get_statistic_boundary(None, []))


class GetTimeDeltaTestCase(unittest.TestCase):

    def test_delta_from_first_message(self):
        timestamp = (datetime.now() - timedelta(days=2, hours=1)).isoformat()
        chat_history = {"messages": [{"timestamp": timestamp}]}
        delta = get_time_delta(chat_history)
        self.assertEqual(2, delta.days)

    def test_no_messages(self):
        self.assertIsNone(get_time_delta({"messages": []}))

    def test_invalid_timestamp(self):
        self.assertIsNone(get_time_delta({"messages": [{"timestamp": "bla"}]}))


if __name__ == '__main__':
    unittest.main()
