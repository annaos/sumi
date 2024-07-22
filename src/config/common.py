import os

# Make sure to add this directory to .gitignore"
HISTORY_SAVE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "chats_history"))

SUMMARY_HOURS_LIMIT = 5

CLEAN_LIMIT_DAYS = 30

CLEAN_FREQUENCY_HOURS = 24

STATISTIC_HOURS = 10

NEW_MESSAGE_HOURS = 2

FELIX_ANSWER_FREQUENCY = 5

AI_MODEL = "gpt-4o-mini"

