"""
WIP
The script to find bad words automatically.

It gets a set of added words and determines tf-idf of words
the it uses K-means algorithm to determin them.

>>> from bad_words_detection_system import *
>>> edits = [Edit(1, {'one':1, 'two': 2}, False), Edit(2, {'three':3}, True)]
>>> db = Database('BWDS', 'amir')
"""
import psycopg2

class Edit(object):
    def __init__(self, rev_id, added_words, reverted):
        self.id = rev_id
        self.added_words = added_words
        self.reverted = reverted


class Database(object):
    """Database"""
    def __init__(self, dbname, dbuser):
        self.dbname = dbname
        self.dbuser = dbuser
        self.initiate_database()

    def initiate_database(self):
        self.execute('CREATE DATABASE bwds;')
        self.execute('CREATE TABLE words (id serial PRIMARY KEY, term varchar, no_documents integer);')

    def execute(self, command, return_result=None):
        conn = psycopg2.connect('dbname=%s user=%s' % (self.dbname, self.dbuser))
        cur = conn.cursor()
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
        for edit in edits:
            for word in edit.added_words:
                bad_edits = Edit(-1, {}, True)
                if not edit.reverted:
                    db.execute('INSERT INTO test (term, no_documents) VALUES (%s, %s)', (word, 1))
                else:
                    bad_edits.added_words[word] = bad_edits.added_words.get(word, 0) + edit.added_words[word]
        print db.execute('SELECT * FROM words;', True)
