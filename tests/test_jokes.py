import unittest
from datetime import datetime, timedelta

from sumi.jokes import _is_time_at_night, _get_due_till_morning


class IsTimeAtNightTestCase(unittest.TestCase):

    def test_night_hours(self):
        for hour, minute in [(0, 0), (3, 0), (7, 30)]:
            with self.subTest(time='%02d:%02d' % (hour, minute)):
                self.assertTrue(_is_time_at_night(datetime(2026, 7, 13, hour, minute)))

    def test_day_hours(self):
        for hour, minute in [(7, 31), (12, 0), (23, 59)]:
            with self.subTest(time='%02d:%02d' % (hour, minute)):
                self.assertFalse(_is_time_at_night(datetime(2026, 7, 13, hour, minute)))


class GetDueTillMorningTestCase(unittest.TestCase):

    def test_at_night_waits_till_same_morning(self):
        now = datetime(2026, 7, 13, 3, 0)
        self.assertEqual(timedelta(hours=4, minutes=30), _get_due_till_morning(now))

    def test_at_day_waits_till_next_morning(self):
        now = datetime(2026, 7, 13, 12, 0)
        self.assertEqual(timedelta(hours=19, minutes=30), _get_due_till_morning(now))

    def test_just_before_morning_end(self):
        now = datetime(2026, 7, 13, 7, 29)
        self.assertEqual(timedelta(minutes=1), _get_due_till_morning(now))

    def test_due_time_is_not_at_night(self):
        for hour in [1, 5, 10, 20]:
            with self.subTest(hour=hour):
                now = datetime(2026, 7, 13, hour, 0)
                due = _get_due_till_morning(now)
                self.assertFalse(_is_time_at_night(now + due + timedelta(minutes=1)))


if __name__ == '__main__':
    unittest.main()
