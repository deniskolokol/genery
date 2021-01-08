# -*- coding: utf-8 -*-

"""Operations with text (including URLs)."""


import re
import uuid
import hmac
import random
from hashlib import md5
from string import ascii_lowercase, digits, punctuation
from itertools import groupby
from urllib import parse

from .containers import distinct_elements

RE_SPACES = re.compile(r'\s+')
RE_DIGITS = re.compile(r'\[[0-9]*\]')
RE_SPECIALSYMB = re.compile(r'[^a-zA-Z0-9]')
RE_AZ09 = re.compile(r'[^a-zA-Z0-9/]')
RE_URLS = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')


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
        Hard cleanup - leave only text without digits,
        special symbols and spaces.
        """
        text = RE_DIGITS.sub(' ', self.text)
        text = RE_SPECIALSYMB.sub(' ', text)
        return RE_SPACES.sub(' ', text).strip()

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
