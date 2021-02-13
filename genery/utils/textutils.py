# -*- coding: utf-8 -*-

"""Operations with text (including URLs)."""


import re
import uuid
import hmac
import random
from hashlib import md5
from string import ascii_lowercase, ascii_letters, digits, punctuation
from itertools import groupby
from urllib import parse

from .containers import distinct_elements

RE_SPACES = re.compile(r'\s+')
RE_DIGITS = re.compile(r'\d+')
RE_SPECIALSYMB = re.compile(r'[^a-zA-Z0-9]')
RE_NOLETTERS = re.compile(r'[^a-zA-Z]')
RE_AZ09 = re.compile(r'[^a-zA-Z0-9/]')
RE_URLS = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


_MAPINGS = None
_REGEX = None
_ACCEPTED = None
LATIN_MAP = {
    u'À': 'A', u'Á': 'A', u'Â': 'A', u'Ã': 'A', u'Ä': 'A', u'Å': 'A',
    u'Æ': 'AE', u'Ç':'C', u'È': 'E', u'É': 'E', u'Ê': 'E', u'Ë': 'E',
    u'Ì': 'I', u'Í': 'I', u'Î': 'I', u'Ï': 'I', u'Ð': 'D', u'Ñ': 'N',
    u'Ò': 'O', u'Ó': 'O', u'Ô': 'O', u'Õ': 'O', u'Ö':'O', u'Ő': 'O',
    u'Ø': 'O', u'Ù': 'U', u'Ú': 'U', u'Û': 'U', u'Ü': 'U', u'Ű': 'U',
    u'Ý': 'Y', u'Þ': 'TH', u'ß': 'ss', u'à':'a', u'á':'a', u'â': 'a',
    u'ã': 'a', u'ä':'a', u'å': 'a', u'æ': 'ae', u'ç': 'c', u'è': 'e',
    u'é': 'e', u'ê': 'e', u'ë': 'e', u'ì': 'i', u'í': 'i', u'î': 'i',
    u'ï': 'i', u'ð': 'd', u'ñ': 'n', u'ò': 'o', u'ó':'o', u'ô': 'o',
    u'õ': 'o', u'ö': 'o', u'ő': 'o', u'ø': 'o', u'ù': 'u', u'ú': 'u',
    u'û': 'u', u'ü': 'u', u'ű': 'u', u'ý': 'y', u'þ': 'th', u'ÿ': 'y'
    }
LATIN_SYMBOLS_MAP = {
    u'©':'(c)',
    }
GREEK_MAP = {
    u'α':'a', u'β':'b', u'γ':'g', u'δ':'d', u'ε':'e', u'ζ':'z', u'η':'h',
    u'θ':'8', u'ι':'i', u'κ':'k', u'λ':'l', u'μ':'m', u'ν':'n', u'ξ':'3',
    u'ο':'o', u'π':'p', u'ρ':'r', u'σ':'s', u'τ':'t', u'υ':'y', u'φ':'f',
    u'χ':'x', u'ψ':'ps', u'ω':'w', u'ά':'a', u'έ':'e', u'ί':'i', u'ό':'o',
    u'ύ':'y', u'ή':'h', u'ώ':'w', u'ς':'s', u'ϊ':'i', u'ΰ':'y', u'ϋ':'y',
    u'ΐ':'i', u'Α':'A', u'Β':'B', u'Γ':'G', u'Δ':'D', u'Ε':'E', u'Ζ':'Z',
    u'Η':'H', u'Θ':'8', u'Ι':'I', u'Κ':'K', u'Λ':'L', u'Μ':'M', u'Ν':'N',
    u'Ξ':'3', u'Ο':'O', u'Π':'P', u'Ρ':'R', u'Σ':'S', u'Τ':'T', u'Υ':'Y',
    u'Φ':'F', u'Χ':'X', u'Ψ':'PS', u'Ω':'W', u'Ά':'A', u'Έ':'E', u'Ί':'I',
    u'Ό':'O', u'Ύ':'Y', u'Ή':'H', u'Ώ':'W', u'Ϊ':'I', u'Ϋ':'Y'
    }
TURKISH_MAP = {
    u'ş':'s', u'Ş':'S', u'ı':'i', u'İ':'I', u'ç':'c', u'Ç':'C', u'ü':'u',
    u'Ü':'U', u'ö':'o', u'Ö':'O', u'ğ':'g', u'Ğ':'G'
    }
RUSSIAN_MAP = {
    u'а':'a', u'б':'b', u'в':'v', u'г':'g', u'д':'d', u'е':'e', u'ё':'yo',
    u'ж':'zh', u'з':'z', u'и':'i', u'й':'j', u'к':'k', u'л':'l', u'м':'m',
    u'н':'n', u'о':'o', u'п':'p', u'р':'r', u'с':'s', u'т':'t', u'у':'u',
    u'ф':'f', u'х':'h', u'ц':'c', u'ч':'ch', u'ш':'sh', u'щ':'sh', u'ъ':'',
    u'ы':'y', u'ь':'', u'э':'e', u'ю':'yu', u'я':'ya', u'А':'A', u'Б':'B',
    u'В':'V', u'Г':'G', u'Д':'D', u'Е':'E', u'Ё':'Yo', u'Ж':'Zh', u'З':'Z',
    u'И':'I', u'Й':'J', u'К':'K', u'Л':'L', u'М':'M', u'Н':'N', u'О':'O',
    u'П':'P', u'Р':'R', u'С':'S', u'Т':'T', u'У':'U', u'Ф':'F', u'Х':'H',
    u'Ц':'C', u'Ч':'Ch', u'Ш':'Sh', u'Щ':'Sh', u'Ъ':'', u'Ы':'Y', u'Ь':'',
    u'Э':'E', u'Ю':'Yu', u'Я':'Ya'
    }
UKRAINIAN_MAP = {
    u'Є':'Ye', u'І':'I', u'Ї':'Yi', u'Ґ':'G', u'є':'ye', u'і':'i', u'ї':'yi',
    u'ґ':'g'
    }
CZECH_MAP = {
    u'č':'c', u'ď':'d', u'ě':'e', u'ň':'n', u'ř':'r', u'š':'s', u'ť':'t',
    u'ů':'u', u'ž':'z', u'Č':'C', u'Ď':'D', u'Ě':'E', u'Ň':'N', u'Ř':'R',
    u'Š':'S', u'Ť':'T', u'Ů':'U', u'Ž':'Z'
    }
POLISH_MAP = {
    u'ą':'a', u'ć':'c', u'ę':'e', u'ł':'l', u'ń':'n', u'ó':'o', u'ś':'s',
    u'ź':'z', u'ż':'z', u'Ą':'A', u'Ć':'C', u'Ę':'e', u'Ł':'L', u'Ń':'N',
    u'Ó':'o', u'Ś':'S', u'Ź':'Z', u'Ż':'Z'
    }
LATVIAN_MAP = {
    u'ā':'a', u'č':'c', u'ē':'e', u'ģ':'g', u'ī':'i', u'ķ':'k', u'ļ':'l',
    u'ņ':'n', u'š':'s', u'ū':'u', u'ž':'z', u'Ā':'A', u'Č':'C', u'Ē':'E',
    u'Ģ':'G', u'Ī':'i', u'Ķ':'k', u'Ļ':'L', u'Ņ':'N', u'Š':'S', u'Ū':'u',
    u'Ž':'Z'
    }

def _make_regex():
    downcode_maps = {}
    downcode_maps.update(LATIN_MAP)
    downcode_maps.update(LATIN_SYMBOLS_MAP)
    downcode_maps.update(GREEK_MAP)
    downcode_maps.update(TURKISH_MAP)
    downcode_maps.update(RUSSIAN_MAP)
    downcode_maps.update(UKRAINIAN_MAP)
    downcode_maps.update(CZECH_MAP)
    downcode_maps.update(POLISH_MAP)
    downcode_maps.update(LATVIAN_MAP)

    symbols = u"".join(downcode_maps.keys())
    regex = re.compile(u"[%s]|[^%s]+" % (symbols, symbols))

    return downcode_maps, regex


def downcode(text):
    """
    'Downcodes' the string passed in the parameter `text`, i.e.
    returns the closest representation of a multilingual text
    only using chars from the basic latin alphabet.

    :param text: <str>
    :return: <str>
    """
    global _MAPINGS, _REGEX

    if not _REGEX:
        _MAPINGS, _REGEX = _make_regex()

    downcoded = ""
    for piece in _REGEX.findall(text):
        if piece in _MAPINGS:
            downcoded += _MAPINGS[piece]
        else:
            downcoded += piece

    return downcoded


def remove_nontext(text):
    """
    :param text: <str>
    :return: <str>
    """
    global _ACCEPTED

    if not _ACCEPTED:
        mapings, _ = _make_regex()
        symbols = list(mapings.keys())
        symbols = u"".join(symbols)

        # Basic allowed symbols.
        _ACCEPTED = symbols + ascii_letters + digits + punctuation

        # Additional allowed symbols.
        _ACCEPTED += "„”–—"

    result = ""
    for piece in text:
        if (piece in _ACCEPTED) or (piece in [" ", "\n", "\r"]):
            result += piece

    return result


def generate_key(*values, delimiter='_'):
    """Generates random UUID and HMACs it with MD5."""
    if not values:
        new_uuid = uuid.uuid4()
    else:
        new_uuid = [str(x)for x in values]
        new_uuid = delimiter.join(new_uuid)

    new_uuid = str(new_uuid).encode('utf-8')

    return hmac.new(new_uuid, digestmod=md5).hexdigest()


def rand_string(size=12):
    """Generates quazi-unique sequence from random digits and letters."""
    return ''.join(random.choice(ascii_lowercase+digits)
                   for x in range(size))


def remove_repeated_punctuation(text):
    """
    Removes repeated puntuation such as '???' or '...'.
    Warning: it will remove '...' from the end of the sentence
             so use only when this isn't necessary.
    """
    result = []
    for key, grouper in groupby(text):
        if key in punctuation:
            result.append(key)
        else:
            result.extend(grouper)

    return ''.join(result)


def smart_truncate(text, limit=100, suffix='...'):
    """
    Truncates a text to the end of the last word before
    reaching `limit`, and adds `suffix` to the end.

    Since it is using Python's slicing, negative values
    work, too.

    :param text: <str>
    :param limit: <int>
    :param suffix: <str>
    :return: <str>
    """
    if len(text) <= limit:
        return text

    return text[:limit].rsplit(' ', 1)[0]+suffix


class TextCleaner:
    """A simple text cleaning util."""
    def __init__(self, text):
        """
        :param text: <str>
        """
        self.text = text
        self.text_clean = self.cleanup()

    def cleanup(self):
        """
        Soft cleanup - leave text intact, but remove
        repeated '\n' and spaces, and finally strip.
        """
        text = ''
        try:
            paragraphs = self.text.split('\n')
        except AttributeError:
            return text

        for par in paragraphs:
            par = par.strip()
            if par == '':
                continue

            par = RE_SPACES.sub(' ', par)
            text += par + '\n'

        return text.strip()

    def cleanup_hard(self):
        """
        Performs hard cleanup: leaves only text without digits,
        special symbols and spaces, downlodes to basic latin
        characters.

        Warning: Use this with caution and for checking only, if
        a text worth saving! Any valuable information that depends
        on numbers and/or special symbols will be lost.
        """
        text = downcode(self.text)
        text = RE_SPECIALSYMB.sub(' ', text)
        text = RE_DIGITS.sub('', text)
        text = RE_SPACES.sub(' ', text)

        return text.strip()

    def extract_urls(self, distinct=True):
        """
        Extracts and cleans up all urls from self.text.

        :param distinct: <bool>
        :return: <list>
        """
        urls = RE_URLS.findall(self.text)
        clean_urls = []
        for url in urls:
            # Get the last character.
            last_char = url[-1]

            # Check if the last character is not an alphabet,
            # or a number, or a '/' (some websites may have that).
            if bool(RE_AZ09.match(last_char)):
                url = url[:-1]
            clean_urls.append(url)

        if distinct:
            clean_urls = distinct_elements(clean_urls, preserve_order=True)

        return clean_urls


class URLNormalizer:
    def __init__(self, url, **kwargs):
        self._parsed = parse.urlparse(url)
        self._uri = ''
        self._domain = ''
        self._domain_name = ''
        if self.is_valid:
            self._uri = url
            self._domain = '{uri.scheme}://{uri.netloc}/'.format(uri=self._parsed)
            self._domain_name = re.sub('.*w\.', '', self._parsed.netloc, 1)

    @property
    def domain(self): return self._domain

    @property
    def uri(self): return self._uri

    @property
    def domain_name(self): return self._domain_name

    @property
    def parsed(self): return self._parsed

    @property
    def is_valid(self):
        return all([self.parsed.scheme, self.parsed.netloc, self.parsed.path])
