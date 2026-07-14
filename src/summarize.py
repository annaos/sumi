import logging

from src.ai import ask_ai
from src.config import VERSION
from src.members.registry import get_sender

logging.basicConfig(format='\n%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

FORMAT_RULES = """
Formatting rules:
- Answer in Russian, matching the informal tone and style of the chat itself.
- Format for Telegram HTML: only <b> (bold) and <i> (italic) are allowed. Never use <br>, <p> or any other tags. Separate paragraphs with an empty line.
- The whole answer must be shorter than 4000 characters.
"""

CHAT_INPUT_DESCRIPTION = """
You are Sumi, an AI participant of a group chat. You will receive the chat messages one per line in the form "sender: message".
"""

SUMMARY_SYSTEM_PROMPT = f"""
{CHAT_INPUT_DESCRIPTION}
Summarize the conversation:
- Identify the main discussion topics, ordered from most to least discussed.
- For each topic write one brief paragraph: start with the topic in <b>bold</b>, then capture the essence of the discussion — who argued for what and how it ended (agreement, open question, joke).
- Base the summary only on the provided messages, never add facts of your own. Keep the participants' names exactly as written.
{FORMAT_RULES}"""

POINT_SUMMARY_SYSTEM_PROMPT = f"""
{CHAT_INPUT_DESCRIPTION}
Summarize only the part of the conversation related to this topic: %s
- Write one or two brief paragraphs: what was said about the topic, who said what, and what conclusion (if any) was reached.
- Ignore unrelated messages. If the topic was barely or never mentioned, honestly say so instead of inventing content.
- Base the summary only on the provided messages, never add facts of your own. Keep the participants' names exactly as written.
{FORMAT_RULES}"""

SHORT_SYSTEM_PROMPT = f"""
{CHAT_INPUT_DESCRIPTION}
Follow this instruction from a chat participant, applying it to the provided messages: %s
{FORMAT_RULES}"""

PROFILE_SYSTEM_PROMPT = f"""
{CHAT_INPUT_DESCRIPTION}
Твоя задача — описать личные качества участника %s на основе его сообщений:
- Опирайся только на сообщения этого участника, приводи конкретные примеры из них.
- Если возможно, укажи предпочтения и политические взгляды участника.
- Ответь не больше чем в четырёх предложениях. Каждое предложение — отдельный абзац.
{FORMAT_RULES}"""

PROFILE_KAI_SYSTEM_PROMPT = f"""
{CHAT_INPUT_DESCRIPTION}
Твоя задача — критично описать личные качества участника %s на основе его сообщений:
- Подходи к анализу критично, не бойся обидеть участника.
- Опирайся только на сообщения этого участника, приводи конкретные примеры из них.
- Если возможно, укажи предпочтения и политические взгляды участника.
- Ответь не больше чем в четырёх предложениях. Каждое предложение — отдельный абзац.
{FORMAT_RULES}"""

def summarize(chat_history, delta, user, point: str = "", prompt: str = ""):
    messages_prompt = _generate_promt(chat_history)
    if point == "" and prompt == "":
        system_promt = SUMMARY_SYSTEM_PROMPT
        handler = "summarize"
    elif prompt != "":
        system_promt = SHORT_SYSTEM_PROMPT % (prompt)
        handler = "prompt"
    else:
        system_promt = POINT_SUMMARY_SYSTEM_PROMPT % (point)
        handler = "summarize"
    logger.info('prompt: %s', system_promt)

    completion = ask_ai(system_promt, messages_prompt, handler)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"
    metadata += f"Model: {completion.model}\n"
    metadata += f"Version: {VERSION}\n"

    return response_content + metadata


def profile(chat_history, user, delta, kai: bool):
    messages_prompt = _generate_promt(chat_history)
    system_promt = PROFILE_KAI_SYSTEM_PROMPT % user.full_name if kai else PROFILE_SYSTEM_PROMPT % user.full_name
    handler = "profile_kai" if kai else "profile"

    completion = ask_ai(system_promt, messages_prompt, handler)

    response_content = completion.choices[0].message.content
    metadata = "\n\n---\n\n"
    metadata += f"Model: {completion.model}\n"
    metadata += f"Version: {VERSION}\n"

    return _create_profile_header(user, delta) + response_content + metadata


def _generate_promt(chat_history):
    messages = ""
    for message in chat_history["messages"]:
        messages += "%s: %s \n" % (message["sender"], message["message"])
    return messages


def create_summarize_header(user, delta, point ="", prompt =""):
    name  = get_sender(user)
    if prompt != "":
        return "На основании последних <b>%s</b> часов:\n\n" % (str(delta))
    if delta is None:
        return "Вот что %s пропустил%s:\n\n"% (name, point)
    if point != "":
        point = " о %s" % point
    return "Саммари за последние <b>%s</b> часа%s которые пропустил %s:\n\n" % (str(delta), point, name)


def _create_profile_header(user, delta):
    name  = get_sender(user)
    return "Вот что я думаю о %s на основании последних %s:\n\n"% (name, str(delta))

