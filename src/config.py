import os

# Make sure to add this directory to .gitignore"
POLL_SAVE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "polls"))
HISTORY_SAVE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "chats_history"))
HISTORY_MEMBERS_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "members_history"))

SUMMARY_HOURS_LIMIT = 5

STATISTIC_HOURS = 10
PROFILE_DAYS = 7

NEW_MESSAGE_MINUTES = 90

MEMBERS_RECONCILE_HOURS = 24

VERSION = "1.0.6"

ACTIVE_ANSWER_FREQUENCY = 5
ALL_ANSWER_FREQUENCY = 100

AI_MODEL = "gpt-5.5"
AI_MODEL_PRO = "gpt-4o"

