import unittest
from datetime import timedelta

from src.helpers.text_to_timedelta import text_to_timedelta
from src.config.common import STATISTIC_HOURS

class MyTestCase(unittest.TestCase):

    def test_text_to_timedelta_hour(self):
        for hour in [2, 4, 16]:
            with self.subTest(hour=hour):
                text = '%dh' % hour
                expected = timedelta(hours=hour)
                self.assertEqual(expected, text_to_timedelta(text))

    def test_text_to_timedelta_minute(self):
        for number in [2, 4, 16]:
            with self.subTest(number=number):
                text = '%dm' % number
                expected = timedelta(minutes=number)
                self.assertEqual(expected, text_to_timedelta(text))

    def test_text_to_timedelta_wrong(self):
        text = 'bla'
        expected = timedelta(hours=STATISTIC_HOURS)
        self.assertEqual(expected, text_to_timedelta(text))

    def test_text_to_timedelta_nothing(self):
        text = ''
        expected = timedelta(hours=STATISTIC_HOURS)
        self.assertEqual(expected, text_to_timedelta(text))



if __name__ == '__main__':
    unittest.main()
