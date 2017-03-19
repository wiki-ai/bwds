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

LANGUAGE_CODES = [
    'en', 'sv', 'nl', 'de', 'fr', 'war', 'ru', 'ceb', 'it', 'es', 'vi',
    'pl', 'ja', 'pt', 'zh', 'uk', 'ca', 'fa', 'no', 'sh', 'fi', 'ar',
    'id', 'cs', 'sr', 'ro', 'ko', 'hu', 'ms', 'tr', 'min', 'eo', 'kk',
    'eu', 'sk', 'da', 'bg', 'he', 'lt', 'hy', 'hr', 'sl', 'et', 'uz',
    'gl', 'nn', 'vo', 'la', 'simple', 'el', 'hi', 'az', 'th', 'ka',
    'ce', 'oc', 'be', 'mk', 'mg', 'new', 'ur', 'tt', 'ta', 'pms', 'cy',
    'tl', 'lv', 'bs', 'te', 'be-tarask', 'br', 'ht', 'sq', 'jv', 'lb',
    'mr', 'is', 'ml', 'zh-yue', 'bn', 'af', 'ba', 'ga', 'pnb', 'cv',
    'fy', 'lmo', 'tg', 'sco', 'my', 'yo', 'an', 'ky', 'sw', 'io', 'ne',
    'gu', 'scn', 'bpy', 'nds', 'ku', 'ast', 'qu', 'als', 'su', 'pa',
    'kn', 'ckb', 'ia', 'mn', 'nap', 'bug', 'arz', 'bat-smg', 'wa',
    'zh-min-nan', 'am', 'map-bms', 'gd', 'yi', 'mzn', 'si', 'fo',
    'bar', 'vec', 'nah', 'sah', 'os', 'sa', 'roa-tara', 'li', 'hsb',
    'pam', 'mrj', 'mhr', 'se', 'mi', 'ilo', 'hif', 'bcl', 'gan', 'rue',
    'ps', 'glk', 'nds-nl', 'bo', 'vls', 'diq', 'fiu-vro', 'bh', 'xmf',
    'tk', 'gv', 'sc', 'co', 'csb', 'hak', 'km', 'kv', 'vep', 'zea',
    'crh', 'zh-classical', 'frr', 'eml', 'ay', 'stq', 'udm', 'wuu',
    'nrm', 'kw', 'rm', 'szl', 'so', 'koi', 'as', 'lad', 'fur', 'mt',
    'dv', 'gn', 'dsb', 'ie', 'pcd', 'sd', 'lij', 'cbk-zam', 'cdo',
    'ksh', 'ext', 'mwl', 'gag', 'ang', 'ug', 'ace', 'pi', 'pag', 'nv',
    'lez', 'frp', 'sn', 'kab', 'ln', 'myv', 'pfl', 'xal', 'krc', 'haw',
    'rw', 'pdc', 'kaa', 'to', 'kl', 'arc', 'nov', 'kbd', 'av', 'bxr',
    'lo', 'bjn', 'ha', 'tet', 'tpi', 'na', 'pap', 'lbe', 'jbo', 'ty',
    'mdf', 'roa-rup', 'wo', 'tyv', 'ig', 'srn', 'nso', 'kg', 'ab',
    'ltg', 'zu', 'om', 'za', 'chy', 'cu', 'rmy', 'tw', 'tn', 'chr',
    'mai', 'pih', 'got', 'xh', 'bi', 'sm', 'ss', 'rn', 'ki', 'pnt',
    'bm', 'iu', 'ee', 'lg', 'ts', 'fj', 'ak', 'ik', 'st', 'sg', 'ff',
    'dz', 'ny', 'ch', 'ti', 've', 'ks', 'tum', 'cr', 'gom', 'lrc',
    'azb', 'or'
]


def strip_interwikilink_prefixes(text):
    return re.sub(r'\[\[\:?' + r'|'.join(LANGUAGE_CODES) + r'\:', '',
                  text)

ALPHABETS = {lang: re.compile(r'[' + alpha + r']')
             for lang, alpha in {
    'az': r'A-Za-zÇçƏəĞğıİÖöŞşÜü',
    'af': r'A-Za-züûöôïîëêè',
    'ar': r'غظضذخثتشرقصفعسنملكيطحزوهدجبا',
    'cs': r'A-Za-zÁáČčĎďÉéĚěÍíŇňÓóŘřŠšŤťÚúŮůÝýŽž',
    'de': r'A-Za-zÄäÖöÜüß',
    'en': r'A-Za-z',
    'es': r'A-Za-zÑñéÉüÜóÓ',
    'et': r'A-Za-zŠšŽžÕõÄäÖöÜü',
    'fa': r'ابپتثجچحخدذرزژسشصآضطظعغفقکگلمنوهی‌يك',
    'fr': r'A-Za-zÀàÂâÆæÄäÇçÉéÈèÊêËëÎîÏïÔôŒœÖöÙùÛûÜüŸÿ',
    'hi': r'कखगघङचछजझञटठडढणतथदधनपफबभमयरलवशषसहळक्षज्ञ:अपआपाइपिईपीउपुऊपूऋपृॠप'
          r'ॄऌपॢॡपॣएपेऐपैओपोऔपौअंपंअःपः',
    'he': r'למנסעפצקרשתםןףץאבגדהוזחטיכך',
    'hu': r'A-Za-zËëÉéÓóÖöŐőÚúÜüŰűÁá',
    'hy': r'ԱաԲբԳգԴդԵեԶզԷէԸըԹթԺժԻիԼլԽխԾծԿկՀհՁձՂղՃճՄմՅյՆնՇշՈոՉչՊպՋջՌռՍսՎվՏտՐր'
          r'ՑցՈՒՈւուՒւՓփՔքևևՕօՖֆ',
    'id': r'A-Za-z',
    'ja': r'\u3000-\u303F'   # Japanese punctuation
          r'\u3040-\u309F'   # Hiragana
          r'\u30A0-\u30FF'   # Katakana
          r'\uFF00-\uFFEF'   # Roman characters and half-width katakana
          r'\u4E00-\u9FCC'   # Unified Ideographs
          r'\u3400-\u4DFF',  # Unified Ideographs Ext A
    'ko': r'\uAC00-\uD7AF'   # Hangul Syllables
          r'\u1100-\u11FF'   # Hangul Jamo
          r'\u3130-\u318F'   # Hangul Compatibility Jamo
          r'\u3200-\u32FF'   # Enclosed CJK Letters and Months
          r'\uA960-\uA97F'   # Hangul Jamo Extended-A
          r'\uD7B0-\uD7FF'   # Hangul Jamo Extended-B
          r'\uFF00-\uFFEF',  # Halfwidth and Fullwidth Forms
    'no': r'A-Za-zÆØÅæøåéèêóòâôüáàé',
    'pl': r'AaĄąBbCcĆćDdEeĘęFfGgHhIiJjKkLlŁłMmNnŃńOoÓóPpRrSsŚśTtUuWwYyZzŹźŻż',
    'pt': r'A-Za-záàâãçéêíóôõúüÁÀÂÃÇÉÊÍÓÔÕÚ',
    'sv': r'A-Za-zÅÄÖåäö',
    'ta': r'௰௱௲௳௴௵௶௷௸௹௺ௗௐொோௌ்ெேைீுூாிரறலளழவஶஷஸஹணதநனபம'
          r'யஐஒஓஔகஙசஜஞடஂஃஅஆஇஈஉஊஎஏ',
    'tr': r'A-Za-zÇĞİÖŞÜçğıöşüâîûÂÎÛ',
    'uk': r'АаБбВвГгҐґДдЕеЄєЖжЗзИиІіЇїЙйКкЛлМмНнОоПпРрСсТтУуФфХхЦцЧчШшЩщЬ'
          r'ьЮюЯя',
    'ur': r'ابپتٹثجچحخدڈذرڑزژسشصضطظعغفقکگلمنوهھءیےٹڈڑ‌آّْیٰوَُِٗ',
    'uz': r'A-Za-zʻ',
    'vi': r'AaĂăÂâBbCcDdĐđEeÊêGgHhIiKkLlMmNnOoÔôƠơPpQqRrSsTtUuƯưVvXxYy',
    'zh': r'\u4E00-\u9FCC'          # Unified Ideographs
          r'\u3400-\u4DFF'          # Unified Ideographs Ext A
          r'\U00020000-\U0002A6DF'  # Unified Ideographs Ext. B
          r'\uF900-\uFAFF'          # Compatibility Ideographs
          r'\U0002F800-\U0002FA1F'  # Compatibility Ideographs Suppl.
}.items()}


def token_contains_lang(token, lang_code):
    return ALPHABETS[lang_code].search(token) is not None
