from telegram import Message

from config.common import FELIX_ANSWER_FREQUENCY
from helpers.util import ask_ai

def answer_felix(message: Message, is_edited: bool):
    if is_edited == False and message.from_user.full_name == "Felix":
        if message.message_id % FELIX_ANSWER_FREQUENCY == 0:
            return _generate_answer(message.text)
    return None


def _generate_answer(message: str):
    sytem = "Ты — участник дискуссионного чата. Придумай короткий остроумный ответ на сообщение основателя чата Феликса."

    completion = ask_ai(sytem, message)

    return completion.choices[0].message.content
