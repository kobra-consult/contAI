from cryptography.hazmat.primitives import serialization
from jwt import ExpiredSignatureError
import configs
import jwt


payload_data = {
    "sub": "1234",
    "name": "Everton Kopec",
    "nickname": "kopec"
}

my_secret = 'kopec'


private_key = open('/home/kopec/.ssh/id_rsa', 'r').read()
key = serialization.load_ssh_private_key(private_key.encode(), password=b'')
try:
    token = jwt.encode(
        payload=payload_data,
        key=key,
        algorithm='RS256'
        )
except ExpiredSignatureError as error:
    print(f'Unable to decode the token, error: {error}')

# print(token)
header_data = jwt.get_unverified_header(token)
print(header_data)
# print(jwt.decode(token, key='kopec', algorithms=['HS256', ]))
result_token = jwt.decode(token, key='kopec', algorithms=[header_data['alg'], ], options={"verify_signature": False})
print(result_token)

class Auth:
    def __init__(self):
        self.tokens_authentication = configs.tokens_authentication
