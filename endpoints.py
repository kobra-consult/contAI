from jwt import ExpiredSignatureError

from auth.authetication import Auth
from flask import Blueprint, Flask, request, jsonify
from flask_cors import CORS, cross_origin
from gpt_core import GPTCore
from openai import AuthenticationError
from utils import utils
import asyncio
import json
import logging

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "http://localhost:5000"}})
app.config['CORS_HEADERS'] = 'Content-Type'
gpt_core_calls = Blueprint('gpt_core', __name__, template_folder='templates')

CORS(gpt_core_calls)
gpt_auth = Auth()
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)


class Endpoints:
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.gpt_core_instance = GPTCore(self.logger)

    @staticmethod
    @gpt_core_calls.route('/api/auth', methods=['POST'])
    def auth():
        data = request.json
        # Add token to the list of valid authentication tokens
        token = gpt_auth.set_jwt_token(data)
        return token

    @staticmethod
    @gpt_core_calls.route('/api/token', methods=['POST'])
    def authenticate():
        data = request.json
        token_authentication = data.get('token', None)
        # Add token to the list of valid authentication tokens
        response, status_code = gpt_auth.check_token(token_authentication)
        return jsonify(response), status_code

    @staticmethod
    @gpt_core_calls.route('/api/start_thread', methods=['POST'])
    def start_new_thread():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            data = request.json
            session_id = data.get('session_id', utils.generate_new_id())
            # Start a new thread and get the thread_id
            thread_id = self.gpt_core_instance.start_thread(session_id)

            return jsonify({'status': 'Thread started', 'session_id': session_id, 'thread_id': thread_id})
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500


    @staticmethod
    @gpt_core_calls.route('/api/approval_lists', methods=['POST'])
    def approved_lists():
        try:
            # Extract data from the request
            data = json.loads(request.data)
            # Generate a new session_id if not provided
            data['session_id'] = data.get('session_id', utils.generate_new_id())

            result = self.gpt_core_instance.approved_lists_core(data)
            response = app.response_class(
                response=result,
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error on Approved_Lists: {unexpected_error}'}), 500


    @staticmethod
    @gpt_core_calls.route('/api/question', methods=['POST'])
    def send_q():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            # Extract data from the request
            data = json.loads(request.data)
            # Generate a new session_id if not provided
            session_id = data.get('session_id', utils.generate_new_id())
            # Check if a thread already exists for the session
            if session_id not in self.gpt_core_instance.context_dict:
                # If not, create a new thread
                thread_id = asyncio.run(self.gpt_core_instance.start_thread(session_id))
            else:
                # If yes, use the existing thread
                thread_id = self.gpt_core_instance.context_dict[session_id]['thread_id']

            # Extract messages from the request
            messages = data.get("content", [])

            # Validate the presence of 'instruction' and 'question' in messages
            for msg in messages:
                if msg.get('instruction') is None and msg.get('question') is None:
                    err = {"error": "Each message in content should have either 'instruction' or 'question'"}
                    response = app.response_class(
                        response=json.dumps(err),
                        status=400,
                        mimetype='application/json')
                    return response

            # Prepare the payload for OpenAI API
            message_payload = [{'role': 'system', 'content': msg['instruction']} for msg in messages if
                               msg.get('instruction')] + \
                              [{'role': 'user', 'content': msg['question']} for msg in messages if msg.get('question')]

            completion = asyncio.run(self.gpt_core_instance.run_questions(session_id, thread_id, message_payload))
            # TODO validate errors
            response = app.response_class(
                response=completion,
                status=200,
                mimetype='application/json'
            )
            header = response.headers
            header['Access-Control-Allow-Origin'] = '*'
            return response
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    @staticmethod
    @gpt_core_calls.route("/api/threads")
    def get_threads():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401
            response = app.response_class(
                response=asyncio.run(self.gpt_core_instance.list_threads()),
                status=200,
                mimetype='application/json')
            return response
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    @staticmethod
    @gpt_core_calls.route("/api/threads-message/<string:thread_id>")
    def get_thread_message(thread_id):
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            thread_message = asyncio.run(self.gpt_core_instance.get_thread_message(thread_id))
            if not json.loads(thread_message)['data']:
                err = {"error": "No thread message"}
                response = app.response_class(
                    response=json.dumps(err),
                    status=404,
                    mimetype='application/json')
                return response

            response = app.response_class(
                response=thread_message,
                status=200,
                mimetype='application/json')
            return response

        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    @staticmethod
    @gpt_core_calls.route('/api/history', methods=['GET'])
    def get_history():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            data = request.args
            session_id = data.get('session_id', utils.generate_new_id())

            if session_id not in self.gpt_core_instance.context_dict:
                return jsonify({'error': 'Invalid session ID'}), 400

            history = self.gpt_core_instance.context_dict[session_id]

            return jsonify({'history': history, 'session_id': session_id})
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    @staticmethod
    @gpt_core_calls.route('/api/feedback', methods=['POST'])
    def user_feedback():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            data = request.json
            session_id = data.get('session_id', utils.generate_new_id())
            user_feedback = data.get('user_feedback', '')

            # TODO
            # Process user feedback (implement)
            # Send feedback to OpenAI to improve the model
            return jsonify({'status': 'Feedback received', 'session_id': session_id})
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    @staticmethod
    @gpt_core_calls.route('/api/reset', methods=['POST'])
    def reset_conversation():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            data = request.json
            session_id = data.get('session_id', utils.generate_new_id())

            # Reset conversation context for the provided session
            self.gpt_core_instance.context_dict[session_id] = {}

            return jsonify({'status': 'Conversation reset', 'session_id': session_id})
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500

    # Endpoint to configure the parameters
    @staticmethod
    @gpt_core_calls.route('/api/config', methods=['POST'])
    def configure_parameters():
        try:
            # token_authentication = request.headers.get('Authorization')
            # if not token_authentication or not token_authentication.startswith('Bearer '):
            #     return jsonify({'error': 'Invalid or missing Bearer token'}), 401
            #
            # token = token_authentication.split(' ')[1]
            # token_checked = gpt_auth.check_token(token)
            # if 'error' in token_checked[0]:
            #     return jsonify(token_checked[0]), 401

            data = request.json
            session_id = data.get('session_id', utils.generate_new_id())
            max_tokens = data.get('max_tokens', 150)

            # Configure parameters for the provided session
            # You can add more configuration logic as needed

            return jsonify({'status': 'Configuration applied', 'session_id': session_id})
        except ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except AuthenticationError:
            return jsonify({'error': 'Authentication failed'}), 401
        except Exception as unexpected_error:
            return jsonify({'error': f'Unexpected error: {unexpected_error}'}), 500
