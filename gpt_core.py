from openai import OpenAI, AsyncOpenAI, RateLimitError, APIStatusError
from token_reports import num_tokens_from_messages
from utils import utils
from dotenv import load_dotenv
from configs import tokens_authentication, context_dict
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


def set_message(session_id, instruction, qa, role='user', response_data=None):
    message = [
        {"role": "system", "content": instruction},
        {"role": role, "content": qa}
    ]
    if response_data:
        message.append({"role": "assistant", "content": response_data})

    context_dict[session_id].append({'role': role, 'content': message})


# Authentication verification function
def verify_authentication(token):
    return token in tokens_authentication


# Function to initiate a new thread
def start_thread(session_id):
    context_dict[session_id] = []


def open_ai_config(API_KEY=None, ORG=None):
    if API_KEY is None:
        API_KEY = utils.get_env("API_KEY")

    if ORG is None:
        ORG = utils.get_env("ORG")

    client_ai = AsyncOpenAI(api_key=API_KEY, organization=ORG)
    return client_ai


async def run_questions(session_id: str, instruction: str, question: str) -> Union[
    str, BaseException, None, RateLimitError, APIStatusError]:
    """
    :param session_id: optional
    :param instruction: required
    :param question: required
    :return: Dict[str, Any] or Exception
    """

    client = open_ai_config()
    try:
        set_message(session_id, instruction, question, 'user')
        completion = await client.chat.completions.create(
            model=model,
            messages=context_dict[session_id],
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


async def list_threads():
    client = open_ai_config()
    completion = await client.beta.threads.create()
    print(completion)
    return completion.json()


async def get_thread_message(thread_id):
    client = open_ai_config()
    completion = await client.beta.threads.messages.list(thread_id=thread_id)
    return completion.json()

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
