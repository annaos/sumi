import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import src.ai_usage as ai_usage


class RecordUsageTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.usage_dir = tmp.name
        patcher = patch("src.ai_usage.AI_USAGE_DIRECTORY", self.usage_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _read(self):
        path = os.path.join(self.usage_dir, "usage_%s.json" % datetime.now().strftime("%Y-%m-%d"))
        with open(path, 'r') as file:
            return json.load(file)

    def test_creates_file_with_handler_entry(self):
        ai_usage.record_usage("summarize", 100, 20)
        self.assertEqual({"summarize": {"in_tokens": 100, "out_tokens": 20, "calls": 1}}, self._read())

    def test_accumulates_same_handler_same_day(self):
        ai_usage.record_usage("summarize", 100, 20)
        ai_usage.record_usage("summarize", 50, 10)
        self.assertEqual({"summarize": {"in_tokens": 150, "out_tokens": 30, "calls": 2}}, self._read())

    def test_keeps_separate_handlers(self):
        ai_usage.record_usage("summarize", 100, 20)
        ai_usage.record_usage("profile", 5, 1)
        data = self._read()
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, data["summarize"])
        self.assertEqual({"in_tokens": 5, "out_tokens": 1, "calls": 1}, data["profile"])


class GetUsageReportTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.usage_dir = tmp.name
        patcher = patch("src.ai_usage.AI_USAGE_DIRECTORY", self.usage_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _write(self, date, data):
        path = os.path.join(self.usage_dir, "usage_%s.json" % date.strftime("%Y-%m-%d"))
        with open(path, 'w') as file:
            json.dump(data, file)

    def test_aggregates_across_days_in_range(self):
        today = datetime.now()
        self._write(today, {"summarize": {"in_tokens": 100, "out_tokens": 20, "calls": 1}})
        self._write(today - timedelta(days=1), {"summarize": {"in_tokens": 50, "out_tokens": 10, "calls": 1}})

        report = ai_usage.get_usage_report(timedelta(days=1))
        self.assertEqual({"in_tokens": 150, "out_tokens": 30, "calls": 2}, report["summarize"])

    def test_ignores_days_outside_range(self):
        today = datetime.now()
        self._write(today, {"summarize": {"in_tokens": 100, "out_tokens": 20, "calls": 1}})
        self._write(today - timedelta(days=5), {"summarize": {"in_tokens": 999, "out_tokens": 999, "calls": 99}})

        report = ai_usage.get_usage_report(timedelta(days=1))
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, report["summarize"])

    def test_empty_when_no_files(self):
        self.assertEqual({}, ai_usage.get_usage_report(timedelta(days=1)))

    def test_keeps_handlers_separate_across_days(self):
        today = datetime.now()
        self._write(today, {"summarize": {"in_tokens": 100, "out_tokens": 20, "calls": 1}})
        self._write(today - timedelta(days=1), {"profile": {"in_tokens": 5, "out_tokens": 1, "calls": 1}})

        report = ai_usage.get_usage_report(timedelta(days=1))
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, report["summarize"])
        self.assertEqual({"in_tokens": 5, "out_tokens": 1, "calls": 1}, report["profile"])


if __name__ == '__main__':
    unittest.main()
