import psycopg2
import os

class Database:

    def __init__(self):

        db_name = os.environ.get('DB_NAME')
        db_user = os.environ.get('DB_USER')
        db_pass = os.environ.get('DB_PASS')

        self.con = psycopg2.connect(database=db_name, user=db_user, password=db_pass)
        self.cur = self.con.cursor()

        # Initialize Tables
        self.cur.execute('''CREATE TABLE IF NOT EXISTS public.progress (
                      u_id INTEGER NOT NULL UNIQUE,
                      progress INTEGER
                    ) WITH (oids = false);''')

        self.cur.execute('''CREATE TABLE IF NOT EXISTS public.comparison (
                      u_id INTEGER NOT NULL,
                      result text,
                      CONSTRAINT comparison_u_id_key UNIQUE(u_id)
                    ) WITH (oids = false);''')

        self.con.commit()

    def set_progress(self, u_id, progress):
        ''' Update progress for user's report '''
        self.cur.execute("UPDATE progress SET progress=%s WHERE u_id=%s",
            (progress, u_id))
        self.con.commit()
        if self.cur.rowcount < 1:
            self.cur.execute('''INSERT INTO progress VALUES(%s, %s)''',
                (u_id, progress))
            self.con.commit()

    def get_progress(self, u_id):
        ''' '''
        self.cur.execute("SELECT progress FROM progress WHERE u_id = %s",
            (u_id,))
        progress = self.cur.fetchone()
        if progress:
            return progress[0]
        else:
            return 0

    def insert_result(self, u_id, result):
        ''' Insert JSON result into comparison table '''
        self.cur.execute('''INSERT INTO comparison VALUES(%s, %s)''',
                (u_id, result))
        self.con.commit()

    def get_result(self, u_id):
        ''' '''
        self.cur.execute("SELECT result FROM comparison WHERE u_id = %s",
            (u_id,))
        result = self.cur.fetchone() 
        if result:
            return result[0]
        else:
            return ''

    def has_result(self, u_id):
        ''' '''
        self.cur.execute("SELECT u_id FROM comparison WHERE u_id = %s",
            (u_id,))
        result = self.cur.fetchone()
        return True if result else False

    def close_con(self):
        ''' Close database connection '''
        self.con.close()

