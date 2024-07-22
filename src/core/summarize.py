import logging

from helpers.util import ask_ai

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

SUMMARY_SYSTEM_PROMPT = f"""
You are a helpful AI assistant that summarizes the chat messages.
Do your best to provide a helpful summary of what was discussed in the provided chat messages.

Reply with a several short paragraphs summarizing what are the main points of the chat messages in russian. Indicate who has what point of view.
"""

def summarize(chat_history, delta):
    messages_prompt = _generate_promt(chat_history)
    # logger.info('prompt: %s', messages_prompt)

    completion = ask_ai(SUMMARY_SYSTEM_PROMPT, messages_prompt)

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

