import logging

from helpers.util import ask_ai

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = """
You are a helpful AI assistant that summarizes the chat messages.
Please identify and summarize the main discussion points from the provided chat messages. 
For each discussion point, create a brief paragraph that clearly and concisely captures the essence of the conversation. 
Focus on delivering a clear and accurate overview of what was discussed in russian.
"""

SHORT_SUMMARY_SYSTEM_PROMPT = """
You are a helpful AI assistant that summarizes the chat messages.
Do your best to provide a helpful summary of what was discussed in the provided chat messages.

Reply with a short paragraph summarizing what are the main points of the chat messages in russian.
"""

def summarize(chat_history, delta):
    messages_prompt = _generate_promt(chat_history)
    system_promt = SUMMARY_SYSTEM_PROMPT
    #if len(chat_history["messages"]) < 150:
    #    system_promt = SHORT_SUMMARY_SYSTEM_PROMPT
    # logger.info('prompt: %s', messages_prompt)

    completion = ask_ai(system_promt, messages_prompt)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"

    metadata += f"Model: {completion.model}\n"
    in_tokens = completion.usage.prompt_tokens
    out_tokens = completion.usage.completion_tokens
    tokens = completion.usage.total_tokens
    price = in_tokens / 1000000 * 15 + out_tokens / 1000000 * 60
    metadata += f"Total price: {price:.2f} cents ({tokens} tokens)\n"

    return _create_header(delta) + response_content + metadata


def _generate_promt(chat_history):
    messages = ""
    for message in chat_history["messages"]:
        messages += "%s: %s \n" % (message["sender"], message["message"])
    return messages


def _create_header(delta):
    if delta is None:
        return "Вот что ты пропустил, пока Марина замьютена:\n\n"
    return "Саммари за последние %s часа, пока Марина замьютена:\n\n" % (str(delta))

