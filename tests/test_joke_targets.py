import tempfile
import unittest
from unittest.mock import patch

from telegram import User

import src.joke_targets as joke_targets

CHAT_ID = -123


def _user(user_id=5, name="Rosa", username="rosa"):
    return User(id=user_id, first_name=name, is_bot=False, username=username)


class JokeTargetsTestCase(unittest.TestCase):

    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        patcher = patch("src.joke_targets.JOKE_TARGETS_DIRECTORY", tmp.name)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_is_target_false_when_never_added(self):
        self.assertFalse(joke_targets.is_target(CHAT_ID, 5))

    def test_is_target_true_after_add(self):
        joke_targets.add_target(CHAT_ID, _user())
        self.assertTrue(joke_targets.is_target(CHAT_ID, 5))

    def test_add_target_ignores_duplicate(self):
        joke_targets.add_target(CHAT_ID, _user())
        joke_targets.add_target(CHAT_ID, _user())
        self.assertEqual(1, len(joke_targets._read_targets_json(CHAT_ID)))

    def test_targets_are_scoped_per_chat(self):
        joke_targets.add_target(CHAT_ID, _user())
        self.assertFalse(joke_targets.is_target(-999, 5))

    def test_remove_target_makes_is_target_false(self):
        joke_targets.add_target(CHAT_ID, _user())
        joke_targets.remove_target(CHAT_ID, 5)
        self.assertFalse(joke_targets.is_target(CHAT_ID, 5))

    def test_remove_target_is_noop_when_not_present(self):
        joke_targets.remove_target(CHAT_ID, 5)
        self.assertEqual([], joke_targets._read_targets_json(CHAT_ID))

    def test_remove_target_only_affects_matching_user(self):
        joke_targets.add_target(CHAT_ID, _user(user_id=5))
        joke_targets.add_target(CHAT_ID, _user(user_id=6, name="Sven", username="sven"))
        joke_targets.remove_target(CHAT_ID, 5)
        self.assertFalse(joke_targets.is_target(CHAT_ID, 5))
        self.assertTrue(joke_targets.is_target(CHAT_ID, 6))


if __name__ == '__main__':
    unittest.main()
