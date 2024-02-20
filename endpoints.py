from flask import Blueprint, Flask, request, jsonify
import asyncio
import gpt_core
import json

app = Flask(__name__)
gpt_core_calls = Blueprint('gpt_core', __name__, template_folder='templates')


@gpt_core_calls.route('/question', methods=['POST'])
def send_q():
    data = json.loads(request.data)
    if "instruction" not in data:
        err = {"error": "No instruction in given data"}
        response = app.response_class(
            response=json.dumps(err),
            status=500,
            mimetype='application/json')
        return response

    if "question" not in data:
        err = {"error": "No question in given data"}
        response = app.response_class(
            response=json.dumps(err),
            status=500,
            mimetype='application/json')
        return response

    completion = asyncio.run(gpt_core.run_questions(data["instruction"], data["question"]))
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
