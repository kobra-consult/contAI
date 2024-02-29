from datetime import datetime
import psycopg2


class DatabaseManager:
    def __init__(self, config):
        self.config = config

    def connect(self):
        """Connect to the PostgresSQL database server"""
        try:
            # connecting to the PostgreSQL server
            with psycopg2.connect(**self.config) as conn:
                print('Connected to the {0} DB'.format(self.config["database"]))
                return conn
        except (psycopg2.DatabaseError, Exception) as error:
            print(error)
            return None

    def insert_session(self, conn, session_id):
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO session (session_id, created_at) VALUES (%s, %s)",
                           (session_id, datetime.utcnow()))

    def insert_thread(self, conn, thread_id, session_id, start_time, end_time, status):
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO thread (thread_id, session_id, start_time, end_time, status) VALUES " 
                           "(%s, %s, %s, %s, %s)", (thread_id, session_id, start_time, end_time, status))

    def insert_statistics(self, conn, role, completion_id, model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint):
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO statistics "
                           "( role, completion_id, created_at, model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint) "
                           " VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                           (role, completion_id, datetime.utcnow(), model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint))

    def insert_message(self, conn, thread_id, role, content, timestamp, statistics_id):
        with conn.cursor() as cursor:
            cursor.execute("INSERT INTO message (thread_id, role, content, timestamp, statistics_id) "
                           "VALUES (%s, %s, %s, %s, %s)",
                           (thread_id, role, content, timestamp, statistics_id))

