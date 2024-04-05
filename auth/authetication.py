from cryptography.hazmat.primitives import serialization
from jwt import ExpiredSignatureError
from jwt.algorithms import get_default_algorithms
import configs
import datetime
import jwt

from utils import utils


class Auth:
    def __init__(self):
        self.tokens_authentication = configs.tokens_authentication
        self.envs = configs.dotenv

    def set_jwt_token(self, payload):
        private_key_path = utils.get_env('PRIVATE_KEY')
        # Load private key for signing
        private_key = open(private_key_path, 'rb').read()
        key_serial = serialization.load_ssh_private_key(private_key, password=None)

        payload['exp'] = (datetime.datetime.now() + datetime.timedelta(seconds=1080)).timestamp()
        try:
            # Encode JWT with private key
            payload_response = {'token': jwt.encode(
                payload=payload,
                key=key_serial,
                algorithm='RS256'
            )}

            return payload_response
        except ExpiredSignatureError as e:
            print(f'Unable to decode the token, error: {e}')

    def check_token(self, token):
        try:
            public_key_path = utils.get_env('PUBLIC_KEY')

            # Load public key for verification
            public_key = open(public_key_path, 'rb').read()
            algorithm = get_default_algorithms().get('RS256')
            public_key_obj = algorithm.prepare_key(public_key)
            jwt.decode(token, key=public_key_obj, algorithms=['RS256'], options={"verify_signature": True})
            return {'status': 'Token valid'}, 200
        except ExpiredSignatureError:
            return {'error': 'Token expired'}, 401
        except Exception as e:
            # Handle other exceptions
            return {'error': f'Unexpected error: {e}'}, 500
