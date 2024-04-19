from datetime import datetime
import psycopg2


class DatabaseManager:
    def __init__(self, config, logger):
        self.config = config
        self.logger = logger

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

    def select_message(self, conn, session_id):
        with conn.cursor() as cursor:
            try:
                cursor.execute("SELECT s.session_id "
                               "     , t.start_time "
                               "     , m.thread_id "
                               "     , m.role "
                               "     , m.content "
                               "FROM contai.session s "
                               "JOIN contai.thread t ON t.session_id = s.session_id "
                               "JOIN contai.message m ON m.thread_id = t.thread_id "
                               "WHERE s.session_id = %s "
                               "  AND m.statistics_id IS NOT NULL "
                               "GROUP BY s.session_id "
                               "       , m.timestamp"
                               "       , t.start_time "
                               "       , m.thread_id "
                               "       , m.role "
                               "       , m.content "
                               "ORDER BY m.timestamp;", (session_id,))
                self.logger.info(f'Select executed - session_id: {session_id}')
                columns = [col[0] for col in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                return results
            except (psycopg2.Error, Exception) as e:
                self.logger.error(f'Error on SELECT_MESSAGE: {e}')

    def upsert_session(self, conn, session_id, created_at):
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO contai.session (session_id, created_at) "
                               "VALUES (%s, %s) "
                               "ON CONFLICT (session_id) DO UPDATE "
                               "SET created_at = EXCLUDED.created_at;",
                               (session_id, created_at))
                conn.commit()
                self.logger.info(f'Session executed - session_id: {session_id}')
            except (psycopg2.Error, Exception) as e:
                self.logger.error(f'Error on UPSERT_SESSION: {e}')

    def upsert_approved_list(self, conn, session_id, id, is_approved, leads_quantity, link, name, synced_at):
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO contai.approved_lists (session_id, id, is_approved, leads_quantity, link, name, synced_at, created_at, updated_at) "
                               "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) "
                               "ON CONFLICT (session_id, id) DO UPDATE "
                               "SET synced_at = EXCLUDED.synced_at "
                               "  , created_at = EXCLUDED.created_at "
                               "  , updated_at = EXCLUDED.updated_at;",
                               (session_id, id, is_approved, leads_quantity, link, name, synced_at, datetime.utcnow(), datetime.utcnow()))
                conn.commit()
                self.logger.info(f'List Approved - session_id: {session_id} List: {id}')
            except (psycopg2.Error, Exception) as e:
                self.logger.error(f"Error on UPSERT_APPROVED_LIST: {e}")

    def insert_thread(self, conn, thread_id, session_id, start_time, end_time, status):
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO contai.thread (thread_id, session_id, start_time, end_time, status) VALUES " 
                               "(%s, %s, %s, %s, %s)", (thread_id, session_id, start_time, end_time, status))
                conn.commit()
                self.logger.info(f'Thread - session_id: {session_id} thread_id: {thread_id}')
            except (psycopg2.Error, Exception) as e:
                print(f"Error on INSERT_THREAD: {e}")

    def insert_statistics(self, conn, statistics_id, role, completion_id, model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint):
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO contai.statistics "
                               "( statistics_id, role, completion_id, created_at, model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint) "
                               " VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)",
                               (statistics_id, role, completion_id, datetime.utcnow(), model, completion_tokens, prompt_tokens, total_tokens, system_fingerprint))
                conn.commit()
                self.logger.info(f'Statistics - statistics_id: {statistics_id}')
            except (psycopg2.Error, Exception) as e:
                self.logger.error(f"Error on INSERT_STATISTICS: {e}")

    def insert_message(self, conn, thread_id, role, content, timestamp, statistics_id=None):
        with conn.cursor() as cursor:
            try:
                cursor.execute("INSERT INTO contai.message (thread_id, role, content, timestamp, statistics_id) "
                               "VALUES (%s, %s, %s, %s, %s)",
                               (thread_id, role, content, timestamp, statistics_id))
                conn.commit()
                self.logger.info(f'Messages - thread_id: {thread_id}')
            except (psycopg2.Error, Exception) as e:
                self.logger.error(f"Error on INSERT_MESSAGE: {e}")

