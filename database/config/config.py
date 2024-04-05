import os.path
from configparser import ConfigParser


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
        # Carrega variáveis de ambiente como configuração
        config = {
            'host': os.getenv('DB_HOST', 'localhost'),
            'database': os.getenv('DB_NAME', 'mydatabase'),
            'user': os.getenv('DB_USER', 'myuser'),
            'password': os.getenv('DB_PASS', 'mypassword'),
            'port': os.getenv('DB_PORT', '5432')
        }
    return config
