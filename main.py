from flask import Flask
from flask_restful import Api, Resource
from endpoints import gpt_core_calls

app = Flask(__name__)
api = Api(app)

app.register_blueprint(gpt_core_calls)

if __name__ == "__main__":
    app.run(debug=True)

