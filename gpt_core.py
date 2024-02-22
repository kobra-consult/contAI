import json
import uuid
from datetime import datetime, timedelta
from openai import OpenAI, AsyncOpenAI, RateLimitError, APIStatusError
from token_reports import num_tokens_from_messages
from utils import utils
from dotenv import load_dotenv
import configs
from typing import Union, Dict, Any
import asyncio
import openai

load_dotenv()

message = [
    {
        "role": "system",
        "content": "You will be provided with a url delimited by triple quotes and a question about the Matrix movie. Your task is to answer the question using only the provided url and to cite the passage(s) of the url used to answer the question."
    },
    {
        "role": "user",
        "content": " '''url: https://en.wikipedia.org/wiki/The_Matrix''' Question: What is the main subject about this movie and give the answer in Portuguese."
    },
]
model = utils.get_env("MODEL")
context_dict = configs.context_dict
threads_dict = configs.threads_dict
tokens_authentication = configs.tokens_authentication


def set_message(session_id, thread_id, instruction, qa, role='user', response_data=None):
    message = [
        {"role": "system", "content": instruction},
        {"role": role, "content": qa}
    ]
    if response_data:
        message.append({"role": "assistant", "content": response_data})

    # Update the context with the message, session, and thread information
    context_dict[session_id].append({
        'role': role,
        'content': message,
        'thread_id': thread_id,
        'timestamp': datetime.utcnow().isoformat() + "Z"
    })


# Authentication verification function
def verify_authentication(token):
    return token in tokens_authentication


def start_thread(session_id):
    thread_id = str(uuid.uuid4())
    start_time = datetime.utcnow().isoformat() + "Z"
    end_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

    # Add the new thread to the threads dictionary
    threads_dict[thread_id] = {
        "session_id": session_id,
        "start_time": start_time,
        "end_time": end_time,
        "status": "active",
        "messages": []
    }

    return thread_id


def open_ai_config(API_KEY=None, ORG=None):
    if API_KEY is None:
        API_KEY = utils.get_env("API_KEY")

    if ORG is None:
        ORG = utils.get_env("ORG")

    client_ai = AsyncOpenAI(api_key=API_KEY, organization=ORG)
    return client_ai


async def run_questions(session_id: str, thread_id: str, instruction: str, question: str) -> Union[
    str, BaseException, None, RateLimitError, APIStatusError]:
    """
    :param session_id: required
    :param thread_id: required
    :param instruction: required
    :param question: required
    :return: Dict[str, Any] or Exception
    """

    client = open_ai_config()
    try:
        set_message(session_id, thread_id, instruction, question, 'user')
        completion = await client.chat.completions.create(
            model=model,
            messages=configs.context_dict[session_id],
            frequency_penalty=1

            # max_tokens=100,
            # temperature=0
        )
        response_data = {
            'id': completion['id'],
            'object': completion['object'],
            'created': completion['created'],
            'model': completion['model'],
            'usage': completion['usage'],
            'system_fingerprint': completion['system_fingerprint']
        }

        set_message(session_id=session_id,
                    instruction='Models answers:',
                    qa=completion['choices'][0]['message']['content'],
                    role='assistant',
                    response_data=response_data)

        return completion.json()
    except openai.APIConnectionError as e:
        print(ValueError("The server could not be reached"))
        return e.__cause__  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError as e:
        print(ValueError("A 429 status code was received; we should back off a bit."))
        return e
    except openai.APIStatusError as e:
        print(ValueError("Another non-200-range status code was received"))
        return e


def list_threads():
    # Fetch information about local threads from context_dict
    local_threads = [
        {
            "session_id": thread_data["session_id"],
            "start_time": thread_data["start_time"],
            "end_time": thread_data["end_time"],
            "status": thread_data["status"],
            "thread_id": thread_id,
        }
        for thread_id, thread_data in context_dict.items()
    ]

    return json.dumps({"local_threads": local_threads})


def get_thread_message(thread_id):
    # Fetch messages from the specified local thread
    if thread_id in context_dict:
        messages = context_dict[thread_id].get("messages", [])
        return json.dumps({"messages": messages})
    else:
        return json.dumps({"error": "Thread not found"}), 404

# keys = utils.read_file("utils/keys_auth.json")

# message = run_questions().choices[0].message.content

# print(num_tokens_from_messages(message))
# thread_id = list_threads()
# print(thread_id)
# print(get_thread_message(thread_id.id))

# async def main() -> None:
#     completion = await run_questions(message)
#     print(completion)
#     print(num_tokens_from_messages(message, model))


# asyncio.run(main())
