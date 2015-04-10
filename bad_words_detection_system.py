"""
WIP
The script to find bad words automatically.

It gets a set of added words and determines tf-idf of words
the it uses K-means algorithm to determin them.

>>> from bad_words_detection_system import *
>>> edits = [Edit(1, {'one':1, 'two': 2}, False), Edit(2, {'three':3}, True)]
>>> db = Database('amirbwds')
>>> bot = Bot(db)
>>> bot.parse_edits(edits)
"""
import psycopg2
import getpass
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


class Edit(object):
    def __init__(self, rev_id, added_words, reverted):
        self.id = rev_id
        self.added_words = added_words
        self.reverted = reverted


class Database(object):
    """Database"""
    def __init__(self, dbuser):
        self.dbname = 'postgres'
        self.dbuser = dbuser
        self.password = getpass.getpass()
        self.initiate_database()

    def initiate_database(self):
        self.execute('DROP DATABASE bwds;')
        self.execute('CREATE DATABASE bwds;')
        self.dbname = 'bwds'
        self.execute('CREATE TABLE words (id serial PRIMARY KEY, term varchar, no_documents integer);')

    # TODO: Use args and kwargs
    def execute(self, command, return_result=None, extra=None):
        conn = psycopg2.connect(database=self.dbname, user=self.dbuser,
                                host='localhost', password=self.password)
        if self.dbname == 'postgres':
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        if extra:
            cur.execute(command, extra)
        else:
            cur.execute(command)
        if return_result:
            res = cur.fetchall()
        else:
            conn.commit()
        cur.close()
        conn.close()
        if return_result:
            return res


class Bot(object):

    def __init__(self, db):
        self.db = db

    def parse_edits(self, edits):
        self.bad_edits = Edit(-1, {}, True)
        for edit in edits:
            for word in edit.added_words:
                if not edit.reverted:
                    self.db.execute("INSERT INTO words (term, no_documents) VALUES (%s, %s)", extra=(word, 1))
                else:
                    self.bad_edits.added_words[word] = bad_edits.added_words.get(word, 0) + edit.added_words[word]
        print self.db.execute("SELECT * FROM words;", return_result=True)
