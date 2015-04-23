"""
WIP
The script to find bad words automatically.

It gets a set of added words and determines tf-idf of words
the it uses K-means algorithm to determin them.

Some parts are copied from
https://github.com/halfak/Objective-Revision-Evaluation-Service/blob/master/ores/label_reverted.py

>>> from bad_words_detection_system import *
>>> edits = [Edit(1, {'one':1, 'two': 2}, False), Edit(2, {'three':3}, True), Edit(3, {'one':5, 'four': 1}, False)]
>>> bot = Bot()
>>> bot.parse_edits(edits)
>>> bot.parse_bad_edits()

python3 bad_words_detection_system.py --rev-pages:f.txt
    --api:https://en.wikipedia.org/w/api.php
    --language:revscoring.languages.english

Use cache:
python3 bad_words_detection_system.py --cache:
"""
import math
import sys
import traceback
import json
import codecs
from importlib import import_module
from collections import OrderedDict
# TODO: User argparse
# import argparse

from mw import api
from mw.lib import reverts

from revscoring.extractors import APIExtractor
from revscoring.datasources import diff


class Edit(object):
    def __init__(self, rev_id, added_words, reverted):
        self.id = rev_id
        self.added_words = added_words
        if not isinstance(self.added_words, dict):
            self.fix_added_words()
        self.reverted = reverted

    def fix_added_words(self):
        temp = {}
        for word in self.added_words:
            temp[word] = temp.get(word, 0) + 1
        self.added_words = temp


class Bot(object):

    def __init__(self, words_cache=None, bad_words_cache=None, no_docs=None):
        self.bad_edits = Edit(-1, {}, True)
        self.counter = 0
        self.words_db = {}
        if bool(bad_words_cache) != bool(words_cache):
            raise "You should define both"
        if words_cache:
            self.cache = True
            self.initiate_cache(words_cache, bad_words_cache, no_docs)
        else:
            self.cache = False

    def initiate_cache(self, words_cache, bad_words_cache, no_docs):
        with codecs.open(words_cache, 'r', 'utf-8') as f:
            self.words_db = json.loads(f.read())
        with codecs.open(bad_words_cache, 'r', 'utf-8') as f:
            self.bad_edits.added_words = json.loads(f.read())
        with codecs.open(no_docs, 'r', 'utf-8') as f:
            self.counter = int(f.read())

    def parse_edits(self, edits):
        for edit in edits:
            #Since edits can be gen and len doesn't mean there
            self.counter += 1
            if edit.reverted:
                for word in edit.added_words:
                    self.bad_edits.added_words[word] = \
                        self.bad_edits.added_words.get(word, 0) + \
                        edit.added_words[word]
                continue
            for word in edit.added_words:
                self.words_db[word] = self.words_db.get(word, 0) + 1

    def parse_bad_edits(self, numbers_to_show=10):
        self.possible_bad_words = {}
        if not self.cache:
            self.counter += 1
        for word in self.bad_edits.added_words:
            if not self.cache:
                self.words_db[word] = self.words_db.get(word, 0) + 1
            self.possible_bad_words[word] = self.tf_idf(word)
        if numbers_to_show:
            self.show_results(numbers_to_show)

    def tf_idf(self, word):
        tf = math.log(self.bad_edits.added_words[word]) + 1
        idf = math.log(float(self.counter)/self.words_db[word])
        return tf*idf

    def show_results(self, numbers_to_show):
        print("Showing %d results" % numbers_to_show)
        values = sorted(self.possible_bad_words.values())
        lim = values[numbers_to_show*-1]
        res = {}
        for word in self.possible_bad_words:
            if self.possible_bad_words[word] >= lim:
                res[word] = self.possible_bad_words[word]
                # print(word, self.possible_bad_words[word])
        res = OrderedDict(sorted(res.items(), key=lambda t: t[1], reverse=True))
        for word in res:
            print(word, res[word])

    def dump(self):
        new_db = {}
        for word in self.bad_edits.added_words:
            new_db[word] = self.words_db[word]
        with codecs.open('words_db.txt', 'w', 'utf-8') as f:
            f.write(json.dumps(new_db))
        with codecs.open('bad_edits_words.txt', 'w', 'utf-8') as f:
            f.write(json.dumps(self.bad_edits.added_words))
        with codecs.open('no_docs.txt', 'w', 'utf-8') as f:
            f.write(json.dumps(self.counter))


def read_rev_pages(f):

    for line in f:
        parts = line.strip().split('\t')

        if len(parts) == 1:
            rev_id = parts
            yield int(rev_id[0]), None
        elif len(parts) == 2:
            rev_id, page_id = parts
            yield int(rev_id), int(page_id)


def import_from_path(path):
    parts = path.split(".")
    module_path = ".".join(parts[:-1])
    attribute_name = parts[-1]

    module = import_module(module_path)

    attribute = getattr(module, attribute_name)

    return attribute


def handle_args():
    args = {}
    for arg in sys.argv[1:]:
        if arg.startswith('--rev-pages:'):
            args['--rev-pages'] = arg[len('--rev-pages:'):]
        elif arg.startswith('--language:'):
            args['--language'] = arg[len('--language:'):]
        elif arg.startswith('--api:'):
            args['--api'] = arg[len('--api:'):]
        elif arg.startswith('--cache:'):
            args['--cache'] = arg[len('--cache:'):]
        elif arg.startswith('--num_res:'):
            args['--num_res'] = arg[len('--num_res:'):]
        else:
            print('Unknown argument')
    return args


def bot_gen(rev_pages, language, api_url):

    session = api.Session(api_url)
    extractor = APIExtractor(session, language=language)

    for rev_id, page_id in rev_pages:
        sys.stderr.write(".")
        sys.stderr.flush()
        try:

            # Detect reverted status
            revert = reverts.api.check(session, rev_id, page_id, radius=3)
            reverted = revert is not None
            added_words = list(
                extractor.extract(rev_id, [diff.added_words]))[0]
            yield Edit(rev_id, added_words, reverted)

        except KeyboardInterrupt:
            sys.stderr.write("\n^C Caught.  Exiting...")
            break

        except:
            sys.stderr.write(traceback.format_exc())
            sys.stderr.write("\n")

    sys.stderr.write("\n")


def cache_parse(pathes, num_res):
    if not pathes.strip():
        pathes = 'words_db.txt,bad_edits_words.txt,no_docs.txt'
    pathes = pathes.split(',')
    bot = Bot(words_cache=pathes[0], bad_words_cache=pathes[1],
              no_docs=pathes[2])
    bot.parse_bad_edits(num_res)


def main():
    args = handle_args()
    if '--num_res' in args:
        num_res = int(args['--num_res'])
    else:
        num_res = 10
    if '--cache' in args:
        cache_parse(args['--cache'], num_res)
        return
    rev_pages = read_rev_pages(open(args['--rev-pages']))

    if args['--language'] is not None:
        language = import_from_path(args['--language'])
    else:
        language = None

    api_url = args['--api']
    gen = bot_gen(rev_pages, language, api_url)
    bot = Bot()
    bot.parse_edits(gen)
    bot.parse_bad_edits(num_res)
    bot.dump()


if __name__ == "__main__":
    main()
