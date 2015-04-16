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
    --api:https://en.wikipedia.org/w/api.php --language:revscoring.languages.english
"""
import math
import sys
import traceback
from importlib import import_module
# TODO: User argparse
# import argparse

from mw import api
from mw.lib import reverts

from revscoring.extractors import APIExtractor
from revscoring.datasources import diff
words_db = {}


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
        print(self.possible_bad_words)

    def tf_idf(self, word):
        return math.log(float(self.counter)/words_db[word])*(math.log(self.bad_edits.added_words[word]) + 1)


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
            added_words = list(extractor.extract(rev_id, [diff.added_words]))[0]
            yield Edit(rev_id, added_words, reverted)

        except KeyboardInterrupt:
            sys.stderr.write("\n^C Caught.  Exiting...")
            break

        except:
            sys.stderr.write(traceback.format_exc())
            sys.stderr.write("\n")

    sys.stderr.write("\n")


def main():
    args = handle_args()
    rev_pages = read_rev_pages(open(args['--rev-pages']))

    if args['--language'] is not None:
        language = import_from_path(args['--language'])
    else:
        language = None

    api_url = args['--api']
    print(language)
    gen = bot_gen(rev_pages, language, api_url)
    bot = Bot()
    bot.parse_edits(gen)
    bot.parse_bad_edits()


if __name__ == "__main__":
    main()
