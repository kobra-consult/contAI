from flask import jsonify

from database.config import config
from database.config.config import load_config
from database.operations.db_operations import DatabaseManager
from datetime import datetime, timedelta
from openai import AsyncOpenAI, RateLimitError, APIStatusError
from typing import Union, Dict, Any, List
from utils import utils
import configs
import json
import openai
import uuid

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


class GPTCore:
    def __init__(self, logger):
        self.logger = logger
        self.model = utils.get_env("MODEL")
        self.context_dict = configs.context_dict
        self.threads_dict = configs.threads_dict
        self.db_config = load_config()
        self.db_manager = DatabaseManager(self.db_config, self.logger)
        self.dotenv = configs.dotenv
        self.conn = None

    def connect_to_db(self):
        """Connect to the database."""
        if not self.conn or self.conn.closed != 0:
            self.conn = self.db_manager.connect()

    def close_db_connection(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.logger.info("Connection to the database closed.")

    @staticmethod
    def open_ai_config(API_KEY=None, ORG=None):

        if API_KEY is None:
            API_KEY = utils.get_env("API_KEY")

        if ORG is None:
            ORG = utils.get_env("ORG")

        client_ai = AsyncOpenAI(api_key=API_KEY, organization=ORG)

        return client_ai

    def set_message(self, session_id, thread_id, messages, response_data=None):
        self.connect_to_db()

        if not self.context_dict.get(session_id):
            self.context_dict[session_id] = {"messages": []}

        if "messages" not in self.context_dict[session_id]:
            self.context_dict[session_id]["messages"] = []

        for msg in messages:
            content = msg.get('content', '')
            role = msg.get('role')
            msg_dict = {'role': role, 'content': content}
            self.context_dict[session_id]["messages"].append(msg_dict)

            if response_data:
                statistics_id = utils.generate_new_id()
                completion_id = response_data['id']
                role = 'assistant'
                completion_tokens = response_data['usage']['completion_tokens']
                model = response_data['model']
                prompt_tokens = response_data['usage']['prompt_tokens']
                total_tokens = response_data['usage']['total_tokens']
                system_fingerprint = response_data['system_fingerprint']
                self.db_manager.insert_statistics(self.conn,
                                                  statistics_id=statistics_id,
                                                  role=role,
                                                  completion_id=completion_id,
                                                  model=model,
                                                  completion_tokens=completion_tokens,
                                                  prompt_tokens=prompt_tokens,
                                                  total_tokens=total_tokens,
                                                  system_fingerprint=system_fingerprint)
                self.context_dict[session_id]["messages"][-1]["statistics"] = {'role': 'assistant',
                                                                               'content': response_data}

                self.db_manager.insert_message(self.conn, thread_id, role, content, datetime.utcnow(), statistics_id)
                continue

            self.db_manager.insert_message(self.conn, thread_id, role, content, datetime.utcnow())

        self.context_dict[session_id]['thread_id'] = thread_id  # Use the new thread key
        self.context_dict[session_id]['timestamp'] = datetime.utcnow().isoformat() + "Z"

    def approved_lists_core(self, data):
        """
        :param data: payload with list of lists approved
        :return: Confirmation of approved lists or Exception
        """

        try:
            # Connect to the database
            self.connect_to_db()
            session_id = data['session_id']
            for lst in data['lists']:
                id = lst['id']
                is_approved = lst['is_approved']
                leads_qty = lst['leads_quantity']
                link = lst['link']
                name = lst['name']
                synced_at = lst['synced_at']
                self.db_manager.upsert_approved_list(self.conn, session_id, id, is_approved, leads_qty, link, name, synced_at)
            return jsonify({'session_id': session_id})
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error on Approved_Lists GPT_CORE: {unexpected_error}'})

    # Authentication verification function
    def verify_authentication(self, token):
        return token in self.tokens_authentication

    async def start_thread(self, session_id):
        # Connect to the database
        self.connect_to_db()

        thread_id = str(uuid.uuid4())
        start_time = datetime.utcnow().isoformat() + "Z"
        end_time = (datetime.utcnow() + timedelta(hours=1)).isoformat() + "Z"

        self.db_manager.upsert_session(self.conn, session_id)
        self.db_manager.insert_thread(self.conn, thread_id, session_id, start_time, end_time, 'active')
        # Add the new thread to the threads dictionary
        self.threads_dict[thread_id] = {
            "session_id": session_id,
            "start_time": start_time,
            "end_time": end_time,
            "status": "active",
            "messages": []
        }
        # Add session_id to context_dict
        self.context_dict[session_id] = {
            "thread_id": thread_id,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        self.logger.info("New thread started - session_id: %s", session_id)
        return thread_id

    async def run_questions(self, session_id: str, thread_id: str, messages: List[Dict[str, str]]) -> Union[
        str, BaseException, None, RateLimitError, APIStatusError]:
        """
        :param session_id: optional
        :param thread_id: unique identifier for the thread
        :param messages: list of message dictionaries containing role, content, and other fields
        :return: Dict[str, Any] or Exception
        """

        try:
            client = self.open_ai_config()
            # Connect to the database
            self.connect_to_db()
            self.set_message(session_id, thread_id, messages)
            completion = await client.chat.completions.create(
                model=self.model,
                messages=messages,
                frequency_penalty=1
                # max_tokens=100,
                # temperature=0
            )

            response_data = {
                'id': completion.id,
                'object': completion.object,
                'created': completion.created,
                'model': completion.model,
                'usage': completion.usage.dict(),
                'system_fingerprint': completion.system_fingerprint
            }
            self.set_message(session_id=session_id,
                             thread_id=thread_id,
                             messages=[{'role': 'assistant', 'content': completion.choices[0].message.content}],
                             response_data=response_data)
            self.logger.info("Question executed - session_id: %s", session_id)
            # print(json.dumps(self.context_dict), "\n\n")
            return json.dumps(self.context_dict)
        except openai.APIConnectionError as e:
            self.logger.error(ValueError("The server could not be reached"))
            return e.__cause__  # an underlying Exception, likely raised within httpx.
        except openai.RateLimitError as e:
            self.logger.error(ValueError("A 429 status code was received; we should back off a bit."))
            return e
        except openai.APIStatusError as e:
            self.logger.error(ValueError("Another non-200-range status code was received"))
            return e

    def list_threads(self):
        # Fetch information about local threads from context_dict
        local_threads = [
            {
                "session_id": thread_data["session_id"],
                "start_time": thread_data["start_time"],
                "end_time": thread_data["end_time"],
                "status": thread_data["status"],
                "thread_id": thread_id,
            }
            for thread_id, thread_data in self.context_dict.items()
        ]

        return json.dumps({"local_threads": local_threads})

    def get_thread_message(self, thread_id):
        # Fetch messages from the specified local thread
        if thread_id in self.context_dict:
            messages = self.context_dict[thread_id].get("messages", [])
            return json.dumps({"messages": messages})
        else:
            return json.dumps({"error": "Thread not found"}), 404

