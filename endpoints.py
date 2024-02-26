from flask import Blueprint, Flask, request, jsonify
from openai import AuthenticationError
import asyncio
import gpt_core
import json

from utils import utils

app = Flask(__name__)
gpt_core_calls = Blueprint('gpt_core', __name__, template_folder='templates')


@gpt_core_calls.route('/api/authenticate', methods=['POST'])
def authenticate():
    data = request.json
    token_authentication = data.get('token', None)

    # Add token to the list of valid authentication tokens
    gpt_core.tokens_authentication.add(token_authentication)

    return jsonify({'status': 'Authentication successful'})


@gpt_core_calls.route('/api/start_thread', methods=['POST'])
def start_new_thread():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())
    # Start a new thread and get the thread_id
    thread_id = gpt_core.start_thread(session_id)

    return jsonify({'status': 'Thread started', 'session_id': session_id, 'thread_id': thread_id})


@gpt_core_calls.route('/api/question', methods=['POST'])
def send_q():
    # Extract data from the request
    data = json.loads(request.data)
    # token_authentication = data.get('token', '')

    try:
        # Verify authentication
        # if not gpt_core.verify_authentication(token_authentication):
        #     return jsonify({'error': 'Invalid authentication'}), 401

        # Generate a new session_id if not provided
        session_id = data.get('session_id', utils.generate_new_session_id())
        # Check if a thread already exists for the session
        if session_id not in gpt_core.context_dict:
            # If not, create a new thread
            thread_id = asyncio.run(gpt_core.start_thread(session_id))
        else:
            # If yes, use the existing thread
            thread_id = gpt_core.context_dict[session_id]['thread_id']


        # Extract messages from the request
        messages = data.get('content', [])

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
        message_payload = [{'role': 'system', 'content': msg['instruction']} for msg in messages if msg.get('instruction')] + \
                          [{'role': 'user', 'content': msg['question']} for msg in messages if msg.get('question')]

        completion = asyncio.run(gpt_core.run_questions(session_id, thread_id, message_payload))
        # TODO validate errors
        response = app.response_class(
            response=completion,
            status=200,
            mimetype='application/json'
        )
        return response
    except AuthenticationError as e:
        # Handle AuthenticationError separately
        return jsonify({'error': 'Authentication failed'}), 401
    except Exception as e:
        print(e)
        # Handle other exceptions
        return jsonify({'error': 'An unexpected error occurred'}), 500


@gpt_core_calls.route("/api/threads")
def get_threads():
    response = app.response_class(
        response=asyncio.run(gpt_core.list_threads()),
        status=200,
        mimetype='application/json')
    return response


@gpt_core_calls.route("/api/threads-message/<string:thread_id>")
def get_thread_message(thread_id):
    thread_message = asyncio.run(gpt_core.get_thread_message(thread_id))
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


@gpt_core_calls.route('/api/history', methods=['GET'])
def get_history():
    data = request.args
    session_id = data.get('session_id', utils.generate_new_session_id())

    if session_id not in gpt_core.context_dict:
        return jsonify({'error': 'Invalid session ID'}), 400

    history = gpt_core.context_dict[session_id]

    return jsonify({'history': history, 'session_id': session_id})


@gpt_core_calls.route('/api/feedback', methods=['POST'])
def user_feedback():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())
    user_feedback = data.get('user_feedback', '')

    # TODO
    # Process user feedback (implement)
    # Send feedback to OpenAI to improve the model

    return jsonify({'status': 'Feedback received', 'session_id': session_id})


@gpt_core_calls.route('/api/reset', methods=['POST'])
def reset_conversation():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())

    # Reset conversation context for the provided session
    gpt_core.context_dict[session_id] = []

    return jsonify({'status': 'Conversation reset', 'session_id': session_id})


# Endpoint to configure the parameters
@gpt_core_calls.route('/api/config', methods=['POST'])
def configure_parameters():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())
    max_tokens = data.get('max_tokens', 150)

    # Configure parameters for the provided session
    # You can add more configuration logic as needed

    return jsonify({'status': 'Configuration applied', 'session_id': session_id})

