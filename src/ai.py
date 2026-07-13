import os

import openai

from src.config import AI_MODEL
from src.utils import get_logger


def ask_ai(system, promt, model = AI_MODEL):
    openai.api_key = os.getenv('OPENAI_TOKEN')
    completion = openai.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": promt}
        ]
    )
    logger = get_logger()
    logger.info(completion)

    return completion
