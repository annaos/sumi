import json
import ollama
import logging

from helpers.nano_to_seconds import nano_to_seconds
from config.ollama import MODEL, SYSTEM_PROMPT

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def summarize(messages):
    messages_json = json.dumps(messages, indent=4, ensure_ascii=False)

    stream = ollama.generate(
        model=MODEL,
        prompt=messages_json,
        system=SYSTEM_PROMPT,
        stream=True
    )

    response_content = ""
    metadata = "\n\n---\n\n"

    try:
        for chunk in stream:
            response_chunk = chunk['response']
            is_done = chunk['done']
            response_content += response_chunk

            if is_done:
                if "model" in chunk:
                    model = chunk['model']
                    metadata += f"Model: {model}\n"

                if "total_duration" in chunk:
                    total_duration_sec = nano_to_seconds(chunk['total_duration'])
                    metadata += f"Total duration: {total_duration_sec:.2f} seconds\n"

                if "load_duration" in chunk:
                    load_duration_sec = nano_to_seconds(chunk['load_duration'])
                    metadata += f"Model load duration: {load_duration_sec:.2f} seconds\n"

                if "prompt_eval_duration" in chunk:
                    prompt_eval_duration_sec = nano_to_seconds(chunk['prompt_eval_duration'])
                    metadata += f"Prompt evaluation duration: {prompt_eval_duration_sec:.2f} seconds\n"

                if "eval_duration" in chunk:
                    eval_duration_sec = nano_to_seconds(chunk['eval_duration'])
                    metadata += f"Response evaluation duration: {eval_duration_sec:.2f} seconds"

        return response_content + metadata
    except Exception:
        logger.exception("An error occurred while generating the summary.")
        return "An error occurred while generating the summary." + response_content
