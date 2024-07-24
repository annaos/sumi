from telegram import Message

from config.common import FELIX_ANSWER_FREQUENCY, ALL_ANSWER_FREQUENCY, FELIX_ANSWER_NAME
from helpers.util import ask_ai

def answer_felix(message: Message, is_edited: bool):
    if is_edited == True:
        return None
    if message.from_user.full_name == FELIX_ANSWER_NAME and message.message_id % FELIX_ANSWER_FREQUENCY == 0:
        return _generate_answer("Феликса", message.text)
    if message.message_id % ALL_ANSWER_FREQUENCY == 0:
        return _generate_answer(message.from_user.first_name, message.text)
    return None


def _generate_answer(sender: str, message: str):
    sytem = f"Ты — участник дискуссионного чата. Придумай короткий остроумный ответ на сообщение участника чата {sender}."

    completion = ask_ai(sytem, message)

    return completion.choices[0].message.content
