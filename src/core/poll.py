import os
import json
from telegram import Poll, Message
from datetime import datetime
from config.common import POLL_SAVE_DIRECTORY
from helpers.util import get_logger

MAX_ANSWERS_IN_FILE = 1000

def create_poll(message: Message, specification: str|None):
    poll = message.poll
    history_options = []
    for option in poll.options:
        history_options.append(option.text)

    file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll.id}.json'
    os.makedirs(os.path.dirname(file_name), exist_ok=True)

    poll_history = {
        "specification": specification,
        "id": poll.id,
        "message_id": message.id,
        "question": poll.question,
        "options": history_options,
        "timestamp": datetime.now().isoformat(),
        "answers": []
    }

    with open(file_name, 'w') as file:
        json.dump(poll_history, file, ensure_ascii=False, indent=2)


def save_anonym_poll_answer(poll: Poll):
    file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll.id}.json'
    logger = get_logger()

    answer_data = {}
    for option in poll.options:
        answer_data[option.text] = option.voter_count
    answer_data["timestamp"] = datetime.now().isoformat()

    try:
        with open(file_name, 'r') as file:
            poll_history = json.load(file)
    except FileNotFoundError:
        logger.error("file history for poll %s not found. Answer %s not saved", poll.id, answer_data)
        return

    if len(poll_history["answers"]) >= MAX_ANSWERS_IN_FILE:
        logger.info("file history for poll %s achieve max length %d. History will be archived", poll.id, MAX_ANSWERS_IN_FILE)
        archived_file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll.id}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        with open(archived_file_name, 'w') as file:
            json.dump(poll_history, file, ensure_ascii=False, indent=2)
        poll_history["answers"] = []

    with open(file_name, 'w') as file:
        poll_history["answers"].append(answer_data)
        json.dump(poll_history, file, ensure_ascii=False, indent=2)


def get_poll_message_id(poll_id):
    file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll_id}.json'
    try:
        with open(file_name, 'r') as file:
            poll_history = json.load(file)
            return poll_history["message_id"]

    except FileNotFoundError:
        logger = get_logger()
        logger.error("file history for poll %s not found. Message id can not be found", poll_id)
        return


def stop_poll(poll_id: str):
    file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll_id}.json'
    try:
        with open(file_name, 'r') as file:
            poll_history = json.load(file)
        archived_file_name = f'{POLL_SAVE_DIRECTORY}/poll_{poll_id}_{datetime.now().strftime("%Y%m%d-%H%M%S")}.json'
        with open(archived_file_name, 'w') as file:
            json.dump(poll_history, file, ensure_ascii=False, indent=2)
            os.remove(file_name)

    except FileNotFoundError:
        logger = get_logger()
        logger.error("file history for poll %s not found. Poll does not archived", poll_id)
        return
