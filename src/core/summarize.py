import os
import logging

from config.common import AI_MODEL, SYSTEM_PROMPT, START_SENTENCE
import openai

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def summarize(chat_history):
    messages = _generate_promt(chat_history)


    OPENAI_TOKEN = os.getenv('OPENAI_TOKEN')

    #messages_prompt = SUM_PROMPT + messages
    messages_prompt = messages

    # logger.info('prompt: %s', messages_prompt)

    openai.api_key = OPENAI_TOKEN
    completion = openai.chat.completions.create(
        model=AI_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": messages_prompt}
        ]
    )
    logger.info(completion)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"

    metadata += f"Model: {completion.model}\n"
    tokens = completion.usage.total_tokens
    price = tokens / 1000000 * 150
    metadata += f"Total price: {price:.2f} cents ({tokens} tokens)\n"

    return START_SENTENCE + response_content + metadata

def _generate_promt(chat_history):
    messages = ""
    for message in chat_history["messages"]:
        messages += "%s: %s \n" % (message["sender"], message["message"])
    return messages
