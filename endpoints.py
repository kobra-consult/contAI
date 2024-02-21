from flask import Blueprint, Flask, request, jsonify
import asyncio
import gpt_core
import json

from utils import utils

app = Flask(__name__)
gpt_core_calls = Blueprint('gpt_core', __name__, template_folder='templates')


@app.route('/api/autenticar', methods=['POST'])
def autenticar():
    data = request.json
    token_autenticacao = data.get('token', None)

    # Adicionar token à lista de tokens de autenticação válidos
    gpt_core.tokens_authentication.add(token_autenticacao)

    return jsonify({'status': 'Autenticação bem-sucedida'})


@gpt_core_calls.route('/api/iniciar_thread', methods=['POST'])
def start_new_thread():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())

    gpt_core.start_thread(session_id)

    return jsonify({'status': 'New thread started', 'session_id': session_id})


@gpt_core_calls.route('/question', methods=['POST'])
def send_q():
    data = json.loads(request.data)
    session_id = data.get('session_id', utils.generate_new_session_id())
    token_authentication = data.get('token', None)

    # Verify authentication
    if not gpt_core.verify_authentication(token_authentication):
        return jsonify({'error': 'Invalid authentication'}), 401

    if "instruction" not in data:
        err = {"error": "No instruction in given data"}
        response = app.response_class(
            response=json.dumps(err),
            status=400,
            mimetype='application/json')
        return response

    if "question" not in data:
        err = {"error": "No question in given data"}
        response = app.response_class(
            response=json.dumps(err),
            status=400,
            mimetype='application/json')
        return response

    completion = asyncio.run(gpt_core.run_questions(session_id, data["instruction"], data["question"]))
    # TODO validate errors
    response = app.response_class(
        response=completion,
        status=200,
        mimetype='application/json'
    )
    return response


@gpt_core_calls.route("/threads")
def get_threads():
    response = app.response_class(
        response=asyncio.run(gpt_core.list_threads()),
        status=200,
        mimetype='application/json')
    return response


@gpt_core_calls.route("/threads-message/<string:thread_id>")
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

    # Process user feedback (implement as needed)
    # For example, you can send feedback to OpenAI to improve the model

    return jsonify({'status': 'Feedback received', 'session_id': session_id})


@gpt_core_calls.route('/api/reset', methods=['POST'])
def reset_conversation():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())

    # Reset conversation context for the provided session
    gpt_core.context_dict[session_id] = []

    return jsonify({'status': 'Conversation reset', 'session_id': session_id})


# Endpoint para configurar parâmetros
@gpt_core_calls.route('/api/configurar', methods=['POST'])
def configure_parameters():
    data = request.json
    session_id = data.get('session_id', utils.generate_new_session_id())
    max_tokens = data.get('max_tokens', 150)

    # Configure parameters for the provided session
    # You can add more configuration logic as needed

    return jsonify({'status': 'Configuration applied', 'session_id': session_id})

