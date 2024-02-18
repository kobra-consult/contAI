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


def open_ai_config():
    client_ai = AsyncOpenAI(api_key=utils.get_env("API_KEY"), organization=utils.get_env("ORG"))
    return client_ai


def run_questions(messages):
    client = open_ai_config()
    try:
        completion = client.chat.completions.create(
            # response_format={"type": "json_object"},
            model=model,
            messages=messages,
            frequency_penalty=1

            # max_tokens=100,
            # temperature=0
        )
        return completion
    except openai.APIConnectionError as e:
        print("The server could not be reached")
        print(e.__cause__)  # an underlying Exception, likely raised within httpx.
    except openai.RateLimitError as e:
        print("A 429 status code was received; we should back off a bit.")
    except openai.APIStatusError as e:
        print("Another non-200-range status code was received")
        print(e.status_code)
        print(e.response)


def list_threads():
    client = open_ai_config()
    completion = client.beta.threads.create()
    return completion


def get_thread_message(thread_id):
    client = open_ai_config()
    completion = client.beta.threads.messages.list(thread_id=thread_id)
    return completion


# keys = utils.read_file("utils/keys_auth.json")

# message = run_questions().choices[0].message.content

# print(num_tokens_from_messages(message))
# thread_id = list_threads()
# print(thread_id)
# print(get_thread_message(thread_id.id))

async def main() -> None:
    completion = await run_questions(message)
    print(completion)
    print(num_tokens_from_messages(message,model))


asyncio.run(main())
