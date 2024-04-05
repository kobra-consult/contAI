import os.path
from configparser import ConfigParser
from urllib.parse import urlparse

def load_config(filename='database.ini', section='postgresql'):

    # get section, default to postgresql
    config = {}
    if os.path.exists(filename):
        parser = ConfigParser()
        parser.read(filename)
        if parser.has_section(section):
            params = parser.items(section)

            for param in params:
                config[param[0]] = param[1]
        else:
            raise Exception('Section {0} not found in the {1} file'.format(section, filename))
    else:
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            url_components = urlparse(db_url)
            config = {
                'user': url_components.username,
                'password': url_components.password,
                'host': url_components.hostname,
                'port': url_components.port,
                'database': url_components.path.lstrip('/')
            }

        return config
