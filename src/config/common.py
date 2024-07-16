import os

# Make sure to add this directory to .gitignore"
HISTORY_SAVE_DIRECTORY = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "saved_data", "chats_history"))

SUMMARY_HOURS_LIMIT = 5

CLEAN_LIMIT_DAYS = 30

CLEAN_FREQUENCY_HOURS = 24

STATISTIC_HOURS = 10

AI_MODEL = "gpt-3.5-turbo"

START_SENTENCE = "Вот что ты пропустил, пока Марина замьютена:\n"

SYSTEM_PROMPT = f"""
You are a helpful AI assistant that summarizes the chat messages.
Do your best to provide a helpful summary of what was discussed in the provided chat messages.

Reply with a short paragraph summarizing what are the main points of the chat messages in russian. Indicate who has what point of view.
"""

# Not used now
SUM_PROMPT = f"""
Отвечай 1-2 короткими абзацеми на русском языке, в котором излагаются основные моменты сообщений чата. Указывай у кого какая точка зрения.
Начинай ответ с: \"{START_SENTENCE}\". Всегда отвечай на русском языке.
"""
