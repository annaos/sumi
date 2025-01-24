import logging

from config.common import VERSION
from helpers.util import ask_ai, get_sender

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """
You are a helpful AI assistant named Sumi that summarizes the chat messages.
Please identify the main discussion points from the provided chat messages.
For each discussion point, create a brief paragraph in russian that clearly and concisely captures the essence of the conversation. Use same style, as in the conversation.
"""

POINT_SUMMARY_SYSTEM_PROMPT = """
You are a helpful AI assistant named Sumi that summarizes the chat messages.
Create a brief paragraph in russian that clearly and concisely captures the essence of the conversation. Use same style, as in the conversation. Focus on %s from the provided chat messages. 
"""

PROFILE_SYSTEM_PROMPT = """
Ты — помощник в групповом чате по имени Суми. Твоя задача оценивать личные качества участника %s на основе его общения. Подходи к анализу критично. Не бойся обидеть участника. Используй тот же стиль общения, что и в сообщениях. Используй конкретные примеры. Если возможно, укажи предпочтения участника. Ответь на русском не больше чем в четырёх предложениях.
"""

SHORT_SUMMARY_SYSTEM_PROMPT = """
You are a helpful AI assistant named Sumi that summarizes the chat messages.
Do your best to provide a helpful summary of what was discussed in the provided chat messages.

Reply with a short paragraph summarizing what are the main points of the chat messages in russian.
"""

def summarize(chat_history, delta, user, point: str):
    messages_prompt = _generate_promt(chat_history)
    if point == "":
        system_promt = SUMMARY_SYSTEM_PROMPT
    else:
        system_promt = POINT_SUMMARY_SYSTEM_PROMPT % (point)
    #if len(chat_history["messages"]) < 150:
    #    system_promt = SHORT_SUMMARY_SYSTEM_PROMPT
    logger.info('prompt: %s', system_promt)

    completion = ask_ai(system_promt, messages_prompt)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"

    metadata += f"Model: {completion.model}\n"
    in_tokens = completion.usage.prompt_tokens
    out_tokens = completion.usage.completion_tokens
    tokens = completion.usage.total_tokens
    price = in_tokens / 1000000 * 15 + out_tokens / 1000000 * 60
    metadata += f"Total price: {price:.2f} cents ({tokens} tokens)\n"
    metadata += f"Version: {VERSION}\n"

    return _create_summarize_header(user, delta, point) + response_content + metadata


def profile(chat_history, user, delta):
    messages_prompt = _generate_promt(chat_history)
    system_promt = PROFILE_SYSTEM_PROMPT % user.full_name

    completion = ask_ai(system_promt, messages_prompt)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"

    metadata += f"Model: {completion.model}\n"
    in_tokens = completion.usage.prompt_tokens
    out_tokens = completion.usage.completion_tokens
    tokens = completion.usage.total_tokens
    price = in_tokens / 1000000 * 15 + out_tokens / 1000000 * 60
    metadata += f"Total price: {price:.2f} cents ({tokens} tokens)\n"
    metadata += f"Version: {VERSION}\n"

    return _create_profile_header(user, delta) + response_content + metadata


def _generate_promt(chat_history):
    messages = ""
    for message in chat_history["messages"]:
        messages += "%s: %s \n" % (message["sender"], message["message"])
    return messages


def _create_summarize_header(user, delta, point =""):
    name  = get_sender(user)
    if point != "":
        point = " о %s" % point
    if delta is None:
        return "Вот что %s пропустил%s:\n\n"% (name, point)
    return "Саммари за последние %s часа%s которые пропустил %s:\n\n" % (str(delta), point, name)


def _create_profile_header(user, delta):
    name  = get_sender(user)
    return "Вот что я думаю о %s на основании последних %s:\n\n"% (name, str(delta))

