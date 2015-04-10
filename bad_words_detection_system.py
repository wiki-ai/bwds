"""
WIP
The script to find bad words automatically.

It gets a set of added words and determines tf-idf of words
the it uses K-means algorithm to determin them.

>>> from bad_words_detection_system import *
>>> edits = [Edit(1, {'one':1, 'two': 2}, False), Edit(2, {'three':3}, True), Edit(3, {'one':5, 'four': 1}, False)]
>>> bot = Bot()
>>> bot.parse_edits(edits)
>>> bot.parse_bad_edits()
"""
import math
words_db = {}


class Edit(object):
    def __init__(self, rev_id, added_words, reverted):
        self.id = rev_id
        self.added_words = added_words
        self.reverted = reverted


class Bot(object):

    def __init__(self):
        self.bad_edits = Edit(-1, {}, True)
        self.counter = 0

    def parse_edits(self, edits):
        for edit in edits:
            #Since edits can be gen and len doesn't mean there
            self.counter += 1
            if edit.reverted:
                for word in edit.added_words:
                    self.bad_edits.added_words[word] = self.bad_edits.added_words.get(word, 0) + edit.added_words[word]
                continue
            for word in edit.added_words:
                words_db[word] = words_db.get(word, 0) + 1

    def parse_bad_edits(self):
        self.possible_bad_words = {}
        self.counter += 1
        for word in self.bad_edits.added_words:
            words_db[word] = words_db.get(word, 0) + 1
            self.possible_bad_words[word] = self.tf_idf(word)
        print self.possible_bad_words

    def tf_idf(self, word):
        return math.log(float(self.counter)/words_db[word])*(math.log(self.bad_edits.added_words[word]) + 1)
