import logging

from revscoring.datasources import Datasource, revision_oriented
from revscoring.datasources.meta import filters, frequencies, gramming, mappers
from revscoring.features import wikitext

from ..wikitext import strip_interwikilink_prefixes, token_contains_lang

logger = logging.getLogger(__name__)


def build_token_gram_types(token_type, lang_code, lower, derepeat, de1337,
                           stemmer, grams):
    orig_r_tokens = wikitext.revision.datasources.tokens_in_types({token_type})
    orig_p_tokens = \
        wikitext.revision.parent.datasources.tokens_in_types({token_type})

    norm_r_tokens = orig_r_tokens
    norm_p_tokens = orig_p_tokens

    if lang_code is not None:
        logger.info("Filtering tokens that do not contain {0}"
                    .format(lang_code))
        norm_r_tokens = filters.filter(
            lambda t: token_contains_lang(t, lang_code), norm_r_tokens)
        norm_p_tokens = filters.filter(
            lambda t: token_contains_lang(t, lang_code), norm_p_tokens)
    if lower:
        norm_r_tokens = mappers.lower_case(norm_r_tokens)
        norm_p_tokens = mappers.lower_case(norm_p_tokens)
    if de1337:
        norm_r_tokens = mappers.de1337(norm_r_tokens)
        norm_p_tokens = mappers.de1337(norm_p_tokens)
    if stemmer:
        norm_r_tokens = mappers.map(stemmer.stem, norm_r_tokens)
        norm_p_tokens = mappers.map(stemmer.stem, norm_p_tokens)
    if derepeat:
        norm_r_tokens = mappers.derepeat(norm_r_tokens)
        norm_p_tokens = mappers.derepeat(norm_p_tokens)

    orig_r_grams = gramming.gram(orig_r_tokens, grams=[tuple(range(0, grams))])
    # p_grams = gramming.gram(p_tokens)
    norm_r_grams = gramming.gram(norm_r_tokens, grams=[tuple(range(0, grams))])
    norm_p_grams = gramming.gram(norm_p_tokens, grams=[tuple(range(0, grams))])

    norm_r_gram_table = frequencies.table(norm_r_grams)
    norm_p_gram_table = frequencies.table(norm_p_grams)

    norm_gram_delta = frequencies.positive(
        frequencies.delta(norm_p_gram_table, norm_r_gram_table))

    return orig_r_grams, norm_r_grams, norm_gram_delta


revision_tokens = Datasource(
    str(wikitext.revision.tokens),
    lambda t: wikitext.revision.tokens.process(
        strip_interwikilink_prefixes(t)),
    depends_on=[revision_oriented.revision.text])
parent_tokens = Datasource(
    str(wikitext.revision.tokens),
    lambda t: wikitext.revision.parent.tokens.process(
        strip_interwikilink_prefixes(t)),
    depends_on=[revision_oriented.revision.parent.text])

solving_context = {revision_tokens, parent_tokens}
