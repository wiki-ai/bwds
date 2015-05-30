#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright Â© 2014 He7d3r
# License: http://he7d3r.mit-license.org/
"""
Extermely under construction.
Some parts are copied from
https://gist.github.com/he7d3r/f99482f4f54f97895ccb/9205f3271fe8daa2f694f4ce3ba9b29213dbad6c
"""
from nltk.tokenize import RegexpTokenizer
from nltk.stem.snowball import SnowballStemmer
import sys
from mw.lib import reverts
from pywikibot import xmlreader
import re

from bad_words_detection_system import Edit, Bot

stemmer = SnowballStemmer('portuguese')
cache = {}

chars = {
    'az': u'A-Za-zÇçƏəĞğıİÖöŞşÜü',
    'de': u'A-Za-zÄäÖöÜüß',
    'en': u'A-Za-z',
    'fa': u'ابپتثجچحخدذرزژسشصآضطظعغفقکگلمنوهی',
    'fr': u'A-Za-zÀàÂâÆæÄäÇçÉéÈèÊêËëÎîÏïÔôŒœÖöÙùÛûÜüŸÿ',
    'pt': u'A-Za-záàâãçéêíóôõúüÁÀÂÃÇÉÊÍÓÔÕÚ',
    'tr': u'A-Za-zÇĞİÖŞÜçğıöşü',
}

def lower(a, lang):
    if lang == 'tr':
       return a.replace('I', u'ı').replace(u'İ','i').lower()
    return a.lower()


def page_info(dump, lang, stemming=False):
    global tokenizer, stemmer
    c = 1
    di_old = []
    di = []
    for entry in dump.parse():
        if entry.ns != '0':
            continue
        if c != entry.id:
            if c != 1:
                di_old = di[:]
            di = []
            if entry.id and int(entry.id[-1]) == 0:
                print('new page', entry.id)
            di.append(entry)
        else:
            di.append(entry)
            continue
        c = entry.id
        firstRev = True
        history = {}
        detector = reverts.Detector(radius=3)
        for revision in di_old:
            stems = set()
            tokenizer = RegexpTokenizer(r'[%s]{3,}' % chars[lang])
            for w in tokenizer.tokenize(revision.text):
                if stemming:
                    if len(w) < 3:
                        continue
                    elif len(w) == 3:
                        stems.add(w.lower())
                        continue
                    else:
                        if w not in cache:
                            cache[w] = stemmer.stem(w)
                        stems.add(cache[w].lower())
                else:
                    stems.add(lower(w, lang))
            if firstRev:
                prevIntersection = stems
                firstRev = False
            added = stems - prevIntersection
            prevIntersection = stems
            history[revision.revisionid] = Edit(
                revision.revisionid, added, False)
            rev = detector.process(revision.text,
                                   {'rev_id': revision.revisionid})
            if rev:
                for reverted in rev.reverteds:
                    history[reverted['rev_id']].reverted = True

        yield history


def run(dumps):
    number = 0
    counter = 0
    bot = Bot()
    for casee in dumps:
        lang = casee.split('/')[-1].split('wiki')[0]
        dump = xmlreader.XmlDump(casee, True)
        for case in page_info(dump, lang):
            counter += 1
            if number and counter > number:
                break
            bot.parse_edits(case.values())
    bot.parse_bad_edits(250)
    bot.dump()

if __name__ == "__main__":
    dumps = sys.argv[1:]
    run(dumps)
