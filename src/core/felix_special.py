from telegram import Message

from config.common import ACTIVE_ANSWER_FREQUENCY, ALL_ANSWER_FREQUENCY
from helpers.util import generate_joke_message, is_active_participant

def answer_felix(message: Message, is_edited: bool):
    if is_edited == True:
        return None
    is_active_message = is_active_participant(message.from_user) and message.message_id % ACTIVE_ANSWER_FREQUENCY == 0
    is_lucky_message = message.message_id % ALL_ANSWER_FREQUENCY == 0
    if is_active_message or is_lucky_message:
        return generate_joke_message(message.from_user, message.text)
    return None
