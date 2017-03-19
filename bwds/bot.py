#!/usr/bin/env python
# -*- coding: UTF-8 -*-
# Copyright Â© 2014 He7d3r
# License: http://he7d3r.mit-license.org/
"""
Extermely under construction.
Some parts are copied from
https://gist.github.com/he7d3r/f99482f4f54f97895ccb/9205f3271fe8daa2f694f4ce3ba9b29213dbad6c
"""

import re
import sys
import time

import regex
from mw.lib import reverts
from nltk.tokenize import RegexpTokenizer

import pywikibot
from bad_words_detection_system import Bot, Edit
from pywikibot import xmlreader


def page_info(dump, lang):
    global tokenizer
    c = 1
    di_old = []
    di = []
    nombre = '3,' if lang not in ['ja', 'zh'] else '1'
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
            revision.text = re.sub(
                r'\[\[(%s)\:' % '|'.join(languages_by_size),
                '',
                revision.text)
            words = set()
            if lang in chars:
                token_pattern = r'[%s]{%s}' % (chars[lang], nombre)
                tokenizer = RegexpTokenizer(token_pattern)
                tokens = tokenizer.tokenize(revision.text)
            else:
                token_pattern = r'\p{alpha}+'
                tokens = regex.findall(token_pattern, revision.text)
            for w in tokens:
                words.add(lower(w, lang))
            if firstRev:
                prevIntersection = words
                firstRev = False
            added = words - prevIntersection
            prevIntersection = words
            history[revision.revisionid] = Edit(
                revision.revisionid, added, False)
            rev = detector.process(revision.text,
                                   {'rev_id': revision.revisionid})
            if rev:
                for reverted in rev.reverteds:
                    history[reverted['rev_id']].reverted = True

        yield history


def run(dumps):
    number = 500000
    counter = 0
    start_time = time.time()
    for casee in dumps:
        lang = casee.split('/')[-1].split('wiki')[0]
        dump = xmlreader.XmlDump(casee, True)
        bot = Bot()
        for case in page_info(dump, lang):
            counter += 1
            if number and counter > number:
                break
            bot.parse_edits(case.values())
    bot.parse_bad_edits(250)
    bot.dump()
    print(time.time() - start_time)
    site = pywikibot.Site('meta', fam='meta')
    page = pywikibot.Page(
        site, 'Research:Revision scoring as a service/Word lists/' + lang)
    try:
        text = page.get()
    except pywikibot.NoPage:
        text = ("{{Research:Revision scoring as a service/template/word list "
                "data\n  |lang=%s\n  |gen=250\n  |badwords=-\n  |informal=-"
                "\n  |stopwords=-\n  |dictionary=-\n  |stemmer=-\n  |contact="
                "\n  |features=no\n  |labels=requested\n  |campaign=no\n  "
                "|needs=-\n  |list-generated=\n  |list-stop=\n}}\n" % lang)
    except:
        return False
    new_text = text
    if re.search(r'\|\s*?list\-generated\s*?\=\s*?', text):
        if re.search(r'\|\s*?list\-generated\s*?\=\s*?(\||\}\})', text):
            new_text = re.sub(
                r'(\|\s*?list\-generated\s*?\=\s*?)(\||\}\})',
                r'\1%s\2' % bot.bad_words_res_text,
                new_text)
    else:
        new_text = re.sub(
            r'\}\}',
            r'|list-generated=%s\n}}' % bot.bad_words_res_text,
            new_text)
    if re.search(r'\|\s*?list\-stop\s*?\=\s*?', text):
        if re.search(r'\|\s*?list\-stop\s*?\=\s*?(\||\}\})', text):
            new_text = re.sub(
                r'(\|\s*?list\-stop\s*?\=\s*?)(\||\}\})',
                r'\1%s\2' % bot.stop_words_res_text,
                new_text)
    else:
        new_text = re.sub(
            r'\}\}',
            r'|list-stop=%s\n}}' % bot.stop_words_res_text,
            new_text)
    if new_text != text:
        page.text = new_text
        page.save('Bot: update results')
if __name__ == "__main__":
    dumps = sys.argv[1:]
    run(dumps)
