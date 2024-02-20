import os

from openai import OpenAI, AsyncOpenAI
from token_reports import num_tokens_from_messages
from utils import utils
from dotenv import load_dotenv
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


def set_message(instruction, question):
    message = [
        {
            "role": "system",
            "content": instruction
        },
        {
            "role": "user",
            "content": question
        },
    ]
    return message


def open_ai_config(API_KEY=None, ORG=None):
    if API_KEY is None:
        API_KEY = utils.get_env("API_KEY")

    if ORG is None:
        ORG = utils.get_env("ORG")

    client_ai = AsyncOpenAI(api_key=API_KEY, organization=ORG)
    return client_ai


async def run_questions(instruction, question):
    client = open_ai_config()
    try:
        message = set_message(instruction, question)
        completion = await client.chat.completions.create(
            # response_format={"type": "json_object"},
            model=model,
            messages=message,
            frequency_penalty=1

            # max_tokens=100,
            # temperature=0
        )
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
