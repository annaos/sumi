import json
import os
import tempfile
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch

import sumi.ai_usage as ai_usage


class RecordUsageTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.usage_dir = tmp.name
        patcher = patch("sumi.ai_usage.AI_USAGE_DIRECTORY", self.usage_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _read(self):
        path = os.path.join(self.usage_dir, "usage_%s.json" % datetime.now().strftime("%Y-%m-%d"))
        with open(path, 'r') as file:
            return json.load(file)

    def test_appends_entry_with_timestamp_and_chat_id(self):
        ai_usage.record_usage("summarize", -100, 100, 20)
        data = self._read()
        self.assertEqual(1, len(data))
        entry = data[0]
        self.assertEqual("summarize", entry["handler"])
        self.assertEqual(-100, entry["chat_id"])
        self.assertEqual(100, entry["in_tokens"])
        self.assertEqual(20, entry["out_tokens"])
        self.assertIn("timestamp", entry)
        datetime.fromisoformat(entry["timestamp"])

    def test_appends_one_entry_per_call(self):
        ai_usage.record_usage("summarize", -100, 100, 20)
        ai_usage.record_usage("summarize", -200, 50, 10)
        data = self._read()
        self.assertEqual(2, len(data))
        self.assertEqual([-100, -200], [entry["chat_id"] for entry in data])


class GetUsageReportTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.usage_dir = tmp.name
        patcher = patch("sumi.ai_usage.AI_USAGE_DIRECTORY", self.usage_dir)
        patcher.start()
        self.addCleanup(patcher.stop)

    def _write(self, date, data):
        path = os.path.join(self.usage_dir, "usage_%s.json" % date.strftime("%Y-%m-%d"))
        with open(path, 'w') as file:
            json.dump(data, file)

    def _entry(self, handler, in_tokens, out_tokens, when=None, chat_id=-100):
        when = when or datetime.now()
        return {"timestamp": when.isoformat(), "handler": handler,
                "chat_id": chat_id, "in_tokens": in_tokens, "out_tokens": out_tokens}

    def test_aggregates_across_days_in_range(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        self._write(today, [self._entry("summarize", 100, 20)])
        self._write(yesterday, [self._entry("summarize", 50, 10, when=yesterday)])

        report = ai_usage.get_usage_report(timedelta(days=2))
        self.assertEqual({"in_tokens": 150, "out_tokens": 30, "calls": 2}, report["summarize"])

    def test_ignores_entries_outside_range(self):
        today = datetime.now()
        old = today - timedelta(days=5)
        self._write(today, [self._entry("summarize", 100, 20)])
        self._write(old, [self._entry("summarize", 999, 999, when=old)])

        report = ai_usage.get_usage_report(timedelta(days=1))
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, report["summarize"])

    def test_filters_by_timestamp_within_day(self):
        now = datetime.now()
        self._write(now, [
            self._entry("summarize", 100, 20, when=now - timedelta(minutes=30)),
            self._entry("summarize", 999, 999, when=now - timedelta(hours=5)),
        ])

        report = ai_usage.get_usage_report(timedelta(hours=1))
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, report["summarize"])

    def test_empty_when_no_files(self):
        self.assertEqual({}, ai_usage.get_usage_report(timedelta(days=1)))

    def test_keeps_handlers_separate_across_days(self):
        today = datetime.now()
        yesterday = today - timedelta(days=1)
        self._write(today, [self._entry("summarize", 100, 20)])
        self._write(yesterday, [self._entry("profile", 5, 1, when=yesterday)])

        report = ai_usage.get_usage_report(timedelta(days=2))
        self.assertEqual({"in_tokens": 100, "out_tokens": 20, "calls": 1}, report["summarize"])
        self.assertEqual({"in_tokens": 5, "out_tokens": 1, "calls": 1}, report["profile"])


if __name__ == '__main__':
    unittest.main()
