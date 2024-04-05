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
        db_url = os.getenv('DATABASE_URL')
        if db_url:
            config['db_url'] = db_url

    if 'db_url' in config:
        return config['db_url']
    else:
        connection_url = "postgres://{user}:{password}@{host}:{port}/{database}".format(**config)
        return config, connection_url
