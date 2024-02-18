import json
import os


def read_file(f):
    f = open(f, "r")
    data_json = json.loads(f.read())
    return data_json


def get_env(var):
    return os.environ.get(var)
