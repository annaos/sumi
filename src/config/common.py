import os

# Make sure to add this directory to .gitignore"
HISTORY_SAVE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "chats_history"))

SUMMARY_HOURS_LIMIT = 0

CLEAN_LIMIT_DAYS = 30

CLEAN_FREQUENCY_HOURS = 24

STATISTIC_HOURS = 10