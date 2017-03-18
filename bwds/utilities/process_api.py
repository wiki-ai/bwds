"""
Generate a datafile of potentially badwords, likely stopwords, and other
features of a set of input revisions by comparing words added in edits
that are reverted with words added in edits that are not reverted.  Assumes
that revisions have a wikitext content model.

Produces a json BLOB file with a few fields:
 - badwords -- A list of potential bad words (most common to reverted edits)
 - stopwords -- A list of potential stopwords (most common overall)

:Usage:
    bwds -h | --help
    bwds --host=<url>
         [--word-limit=<num>]
         [--token-type=<type>]
         [--norm-lower]
         [--norm-derepeat]
         [--norm-de1337]
         [--norm-stem=<lang>]
         [--grams=<num>]
         [--processes=<num>]
         [--input=<path>]
         [--output=<path>]
         [--verbose]
         [--debug]

:Options:
    --host=<url>             The host URL of the MediaWiki install where an API
                             can be found.
    --word-limit=<num>       Limit the number of words output in word lists to
                             this number [default: 1000]
    --token-type=<type>      Limit the tokens processed to this type
                             [default: word]
    --norm-stem=<lang>       If set, use the stemmer for <lang> on words before
                             processing
    --norm-lower             User `lower()` to normalize all words before
                             processing
    --norm-derepeat          Singularize repeated characters within the word
                             before processing
    --grams=<num>            Produce ngrams of words of this length
                             [default: 1]
    --processes=<num>        The number of parallel processes to start for
                             processing edits. [default: <cpu_count>]
    --input=<path>           The path to a file containing rev_ids to process
                             [default: <stdin>]
    --output=<path>          The path to write output to [default: <stdout>]
    --verbose                Prints dots and stuff to <stderr>
    --debug                  Prints debug logs to stderr

"""
import json
import logging
import sys
from collections import defaultdict
from itertools import islice
from multiprocessing import cpu_count

import docopt
import mwapi
import para
from nltk.stem.snowball import SnowballStemmer
from revscoring.datasources.meta import frequencies, gramming, mappers
from revscoring.dependencies import draw
from revscoring.extractors import api
from revscoring.features import wikitext

logger = logging.getLogger(__name__)


def main(argv=None):
    args = docopt.docopt(__doc__, argv=argv)

    logging.basicConfig(
        format='%(asctime)s %(levelname)s:%(name)s -- %(message)s'
    )
    logger.setLevel(logging.DEBUG if args['--debug'] else logging.WARNING)

    api_host = args['--host']

    if args['--input'] == "<stdin>":
        revisions = (json.loads(line) for line in sys.stdin)
    else:
        revisions = (json.loads(line) for line in open(args['--input']))

    if args['--output'] == "<stdout>":
        wordstats_f = sys.stdout
    else:
        wordstats_f = open(args['--output'], 'w')

    word_limit = int(args['--word-limit'])
    token_type = args['--token-type']
    norm_lower = bool(args['--norm-lower'])
    norm_derepeat = bool(args['--norm-derepeat'])
    norm_de1337 = bool(args['--norm-de1337'])
    stem_lang = args['--norm-stem']

    grams = int(args['--grams'])

    if args['--processes'] == "<cpu_count>":
        processes = cpu_count()
    else:
        processes = int(args['--processes'])

    verbose = bool(args['--verbose'])
    run(api_host, revisions, wordstats_f, word_limit, token_type,
        norm_lower, norm_derepeat, norm_de1337, stem_lang, grams,
        processes, verbose)


def run(api_host, revisions, wordstats_f, word_limit, token_type, norm_lower,
        norm_derepeat, norm_de1337, stem_lang, grams, processes, verbose):

    # Construct our API session
    session = mwapi.Session(
        api_host, user_agent="wiki-ai/editquality -- bwds script")
    extractor = api.Extractor(session)

    if stem_lang is not None:
        stemmer = SnowballStemmer(stem_lang)
    else:
        stemmer = None

    # Construct the revision processor
    process_revisions = revision_processor(
        extractor, token_type, norm_lower, norm_derepeat, norm_de1337,
        stemmer, grams)

    # Construct dictionaries for tracking frequencies and mappings between
    # processed revisions
    bad_grams = defaultdict(int)
    grams = defaultdict(int)
    norms = defaultdict(set)

    logging.info("Processing revisions")
    revision_chunks = chunk(revisions, 50)
    revision_delta_norms = para.map(process_revisions, revision_chunks,
                                    mappers=processes)

    for rev, freq_delta, norm_map in revision_delta_norms:
        if rev['reverted_for_damage']:
            logger.debug(
                str(rev['rev_id']) +
                " was reverted for damage and added the following words " +
                str([str(k[0]) for k in freq_delta.keys()]))
        for gram, delta in freq_delta.items():
            if rev['reverted_for_damage']:
                bad_grams[gram] += delta
            grams[gram] += delta

        for gram, originals in norm_map.items():
            for o in originals:
                norms[gram].add(o)

    logging.info("Sorting grams by badness and frequency")
    gram_badness = (((freq + 1) / (grams[gram] + 10), gram)
                    for gram, freq in bad_grams.items())
    limited_badword_grams = \
        islice(sorted(gram_badness, reverse=True), 100)
    print(list(limited_badword_grams))

    gram_badness = (((freq + 1) / (grams[gram] + 10), gram)
                    for gram, freq in bad_grams.items())
    limited_badword_grams = \
        islice(sorted(gram_badness, reverse=True), word_limit)

    gram_freq = ((freq, gram) for gram, freq in grams.items())
    limited_stop_grams = islice(sorted(gram_freq, reverse=True), word_limit)

    badwords = [{'gram': list(gram),
                 'originals': [list(g) for g in norms[gram]],
                 'badness': round(badness, 3)}
                for badness, gram in limited_badword_grams]
    stopwords = [{'gram': list(gram),
                  'originals': [list(g) for g in norms[gram]],
                  'freq': freq}
                 for freq, gram in limited_stop_grams]

    json.dump({'badwords': badwords, 'stopwords': stopwords}, wordstats_f,
              indent=2)


def revision_processor(extractor, token_type, norm_lower, norm_derepeat,
                       norm_de1337, stemmer, grams):

    orig_r_tokens = wikitext.revision.datasources.tokens_in_types({token_type})
    orig_p_tokens = \
        wikitext.revision.parent.datasources.tokens_in_types({token_type})

    norm_r_tokens = orig_r_tokens
    norm_p_tokens = orig_p_tokens

    if norm_lower:
        norm_r_tokens = mappers.lower_case(norm_r_tokens)
        norm_p_tokens = mappers.lower_case(norm_p_tokens)
    if norm_de1337:
        norm_r_tokens = mappers.de1337(norm_r_tokens)
        norm_p_tokens = mappers.de1337(norm_p_tokens)
    if stemmer:
        norm_r_tokens = mappers.map(norm_r_tokens, stemmer.stem)
        norm_p_tokens = mappers.map(norm_p_tokens, stemmer.stem)
    if norm_derepeat:
        norm_r_tokens = mappers.derepeat(norm_r_tokens)
        norm_p_tokens = mappers.derepeat(norm_p_tokens)

    r_grams = gramming.gram(orig_r_tokens, grams=[tuple(range(0, grams))])
    # p_grams = gramming.gram(p_tokens)
    norm_r_grams = gramming.gram(norm_r_tokens, grams=[tuple(range(0, grams))])
    norm_p_grams = gramming.gram(norm_p_tokens, grams=[tuple(range(0, grams))])

    logger.info("Grams: ")
    logger.info(draw(r_grams))
    logger.info("Normalized grams: ")
    logger.info(draw(norm_r_grams))

    norm_r_gram_table = frequencies.table(norm_r_grams)
    norm_p_gram_table = frequencies.table(norm_p_grams)

    norm_gram_delta = frequencies.positive(
        frequencies.delta(norm_p_gram_table, norm_r_gram_table))

    def _process_revisions(revisions):
        rev_ids = [r['rev_id'] for r in revisions]

        error_values = extractor.extract(
            rev_ids, [r_grams, norm_r_grams, norm_gram_delta])

        for (error, values), revision in zip(error_values, revisions):
            if error is None:
                orig_r, norm_r, freq_delta = values
                norm_map = defaultdict(set)
                for original, gram in zip(orig_r, norm_r):
                    norm_map[gram].add(original)

                yield revision, freq_delta, norm_map
            else:
                logger.warning("{0} while solving for {1}"
                               .format(error, revision['rev_id']))

    return _process_revisions


def chunk(iterable, size):
    while True:
        batch = list(islice(iterable, size))
        if len(batch) == 0:
            break
        else:
            yield batch
