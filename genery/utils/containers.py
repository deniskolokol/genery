# -*- coding: utf-8 -*-

"""Operations with container-like classes (lists, dictionaries, etc.)"""

import re
import json
from datetime import datetime
from collections import Mapping, MutableMapping


class RecordDict(dict):
    """
    Dictionary that acts like a class with keys accessed as attributes.
    i.e. `inst['foo']` and `inst.foo` is the same.
    """
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        for key, val in self.items():
            self[key] = self._objectify_recoursive(val)
        self.__dict__ = self

    def _restructure(self, new_dict):
        for key in list(self.keys()):
            del self[key]

        for key, val in new_dict.items():
            self[key] = self._objectify_recoursive(val)
        self.__dict__ = self

    def exclude(self, *args):
        for key in args:
            del self[key]
        return self

    def _objectify_recoursive(self, branch):
        if isinstance(branch, dict):
            for key, val in branch.items():
                branch[key] = self._objectify_recoursive(val)
        elif isinstance(branch, (list, tuple)):
            result = []
            for elem in branch:
                elem = self._objectify_recoursive(elem)
                result.append(elem)
            return result

        else:
            return branch

        return self.__class__(**branch)

    @classmethod
    def from_list(cls, container, key, val):
        """
        Converts a list of <dict>'s (`container`) to <RecordDict>
        whose `container[key]` become keys (warning: should be unique
        and scalar), and corresponding `container[val]` become values.

        Example:
        In [1]: input = [
            {'element': 'akash', 'consort': {'id': 'Bhumi', 'sense': 'sound'}},
            {'element': 'vayu', 'consort': {'id': 'Lehari', 'sense': 'touch'}},
            {'element': 'agni', 'consort': {'id': 'Swaha', 'sense': 'sight'}},
            {'element': 'varuna', 'consort': {'id': 'Varuni', 'sense': 'taste'}},
            {'element': 'bhumi', 'consort': {'id': 'Dyaus', 'sense': 'smell'}},
            ]
        In [2]: obj = RecordDict.from_list(input, key='element', val='consort')
        In [3]: obj
        Out[3]:
         {'akash': {'id': 'Bhumi', 'sense': 'sound'},
          'vayu': {'id': 'Lehari', 'sense': 'touch'},
          'agni': {'id': 'Swaha', 'sense': 'sight'},
          'varuna': {'id': 'Varuni', 'sense': 'taste'},
          'bhumi': {'id': 'Dyaus', 'sense': 'smell'}}

        # And therefore the following calls are possible:

        In [4]: obj.akash
        Out[4]: {'id': 'Bhumi', 'sense': 'sound'}

        In [5]: obj.agni.id
        Out[5]: 'Swaha'

        In [6]: obj.bhumi.sense
        Out[7]: 'smell'

        :param container: <list> of <dict>'s
        :param key: <str> - key name which contains unique values
                            for the whole `container`
        :param val: <str> - key name for value items (do not have
                            to be unique)
        """
        kwargs = dict((s[key], s[val]) for s in container)
        return cls(**kwargs)

    @classmethod
    def from_list_aggregate(cls, container, key, val):
        """
        Similar to `self.from_list`, but act on lists, whose `key`
        is not unique accross the container, gathering values from
        the same keys in lists.

        Example:
        In [1]: input = [
            {'label': 'GPE', 'text': 'Philippines'},
            {'label': 'GPE', 'text': 'Nigeria'},
            {'label': 'GPE', 'text': 'Turkey'},
            {'label': 'ORG', 'text': 'FSC'},
            {'label': 'ORG', 'text': 'EAGF'}
            ]
        In [2]: obj = RecordDict.from_list_aggregate(input, key='label', val='text')
        In [3]: obj
        Out[3]: {
            'GPE': ['Philippines', 'Nigeria', 'Turkey'],
            'ORG': ['FSC', 'EAGF']}
        :param container: <list> of <dict>'s
        :param key: <str> - key name which becomes a key of the result
        :param val: <str> - key name for value items to be aggregated
                            in the list
        """
        kwargs = {}
        for rec in container:
            try:
                kwargs[rec[key]].append(rec[val])
            except (KeyError, AttributeError):
                kwargs[rec[key]] = [rec[val]]
        return cls(**kwargs)

    def lookup(self, *paths, default=None, delimiter='.'):
        """
        Iterates through *paths and return the first found value
        from a nested dictionary with the help of key path.

        Example:
        In [1]: data = RecordDict(**{
            'geo': {
                'gpe': ['Philippines', 'Nigeria', 'Turkey'],
                'loc': ['Mississippi', 'Himalaya'],
            },
            'lang': {
                'en': {
                    'label': 'Eng',
                    'native': 'English'
                },
                'pl': {
                    'label': 'Polish',
                    'native': 'Polski'
                }
            }
        })

        In [2]: data.lookup('lang.pl.native')
        Out[2]: 'Polski'

        In [3]: data.lookup('geo/gpe', delimiter='/')
        Out[3]: ['Philippines', 'Nigeria', 'Turkey']

        In [4]: paths = ['lang.cz.label', 'gorgonzola', 'lang.en.label', 'wu']
        In [5]: data.lookup(*paths)
        Out[4]: 'Eng'
        """
        result = default
        for path in paths:
            result = self._lookup(path, default, delimiter)
            if result != default:
                return result

        return result

    def _lookup(self, path, default=None, delimiter='.'):
        """
        The engine behind self.lookup: returns the value from
        a nested dictionary with the help of key path.
        """
        path = path.split(delimiter)
        if len(path) == 1:
            return self.get(path[0], default)

        # Assume that `path` is a list of recursively accessible dicts.
        def _get_one_level(key_list, level, container):
            if level >= len(key_list):
                if level > len(key_list):
                    raise IndexError
                return container[key_list[level-1]]

            return _get_one_level(key_list,
                                  level+1,
                                  container[key_list[level-1]])

        try:
            return _get_one_level(path, 1, self)
        except KeyError:
            return default

    def flatten(self, separator='_'):
        """
        Flattens nested structure, concatenating keys with separator.
        Warning: destructive - irreversibly changes the structure of
                 the `self`.

        Example:
        In [1]: data = RecordDict(**{
            'name': 'Report Summaries Departement',
            'lang': {
                'label': 'en',
                'name': 'English'
            },
            "place": {
                "id": "85632997",
                "placetype": "country",
                "name": "Belgium",
                "belongsto": ["Europe"],
                "location": {
                    "lon": 4.66092,
                    "lat": 50.640991
                }
            }
        })
        In [2]: data.flatten()
        In [3]: data
        Out[2]:
        {'name': 'Report Summaries Departement',
         'lang_label': 'en',
         'lang_name': 'English',
         'place_id': '85632997',
         'place_placetype': 'country',
         'place_name': 'Belgium',
         'place_belongsto': ['Europe'],
         'place_location_lon': 4.66092,
         'place_location_lat': 50.640991}

         :return: None
         """
        flat = flatten_dict(self, separator=separator)
        self._restructure(flat)

    def update(self, new_dict):
        """Override .update() with the behavior of deep_update."""
        deep_update(self, new_dict)


def objectify(method):
    """Decorator that converts <dict> to instance of <RecordDict>."""
    def objectify_wrapper(*args, **kwargs):
        result = method(*args, **kwargs)
        if isinstance(result, dict):
            result = RecordDict(**result)
        elif isinstance(result, (list, tuple)):
            type_ = type(result)
            result = type_(RecordDict(**elm) for elm in result)

        return result
    return objectify_wrapper


def sniff_json(val):
    try:
        json.dumps(val)
    except TypeError:
        return False
    else:
        return True


def _serialize_recoursive(branch):
    if sniff_json(branch):
        return branch

    if isinstance(branch, dict):
        for key, val in branch.items():
            branch[key] = _serialize_recoursive(val)
    elif isinstance(branch, (list, tuple)):
        result = []
        for elem in branch:
            elem = _serialize_recoursive(elem)
            result.append(elem)
        return result

    else:
        if isinstance(branch, datetime):
            branch = branch.isoformat()
        else:
            branch = str(branch)

    return branch


def prepare_to_serialize(dict_):
    """
    Prepares dict to be serialized to JSON, reducing to
    string any struct object (datetime, ObjectID, etc.).

    :param dict_: <dict>
    :return: <dict> of the same structure
    """
    if sniff_json(dict_):
        return dict_

    return _serialize_recoursive(dict_)


def flatten_dict(dict_, parent_key='', separator='_'):
    items = []
    for key, val in dict_.items():
        new_key = '{0}{1}{2}'.format(parent_key, separator, key) if parent_key else key
        if isinstance(val, MutableMapping):
            items.extend(
                flatten_dict(val, new_key, separator=separator).items()
                )
        else:
            items.append((new_key, val))

    return dict(items)


def flatten_list(list_):
    """
    Flattens out nested lists and tuples (tuples are
    converted to lists for this purpose).

    Example:
    In [1]: flatten_list([1, [[2, 3], [4, 5]], 6])
    Out[1]: [1, 2, 3, 4, 5, 6]
    """
    items = []
    for element in list_:
        if isinstance(element, (list, tuple)):
            items.extend(flatten_list(list(element)))
        else:
            items.append(element)

    return items


def ensure_dict(obj):
    assert isinstance(obj, (dict, str)), "Wrong type: must be string or dict"
    if isinstance(obj, str):
        return json.loads(obj)

    return obj


def ensure_list(obj):
    if isinstance(obj, (list, tuple)):
        return obj

    if isinstance(obj, dict):
        obj = flatten_dict(obj, parent_key='', separator='_')
        return flatten_list([[k, v] for k, v in obj.items()])

    return [obj]


def distinct_elements(container, preserve_order=False):
    """
    Returns distinct elements from sequence
    while preserving the order of occurence.
    """
    if not preserve_order:
        return list(set(container))

    seen = set()
    seen_add = seen.add
    return [x for x in container if not (x in seen or seen_add(x))]


def deep_update(source, overrides):
    """
    Updates a nested dictionary or similar mapping.
    Modifies `source` in place.
    """
    for key, value in overrides.items():
        if isinstance(value, Mapping) and value:
            returned = deep_update(source.get(key, {}), value)
            source[key] = returned
        else:
            source[key] = overrides[key]

    return source


def normalize_keys(dict_, lowercase=True, separator='_'):
    """
    Recoursively changes keys to their normalized version:
    - replaces any special symbol by `separator`
    - lowercases (if necessary).

    Example:
    In [1]: input_ = {"Content-Type": "text/html",
       ...:     "Last-Modified": {
       ...:          "Day-Of-Week": "Sat",
       ...:          "Day": 4,
       ...:          "Month": "Apr"
       ...:     }
       ...: }
    Out[1]:
    {'content_type': 'text/html',
     'last_modified': {'day_of_week': 'Sat', 'day': 4, 'month': 'Apr'}}
    """
    normalized = {}
    for key, val in dict_.items():
        new_key = re.sub('[^A-Za-z0-9]+', separator, key)
        new_key = new_key.lower() if lowercase else new_key

        if isinstance(val, dict):
            val = normalize_keys(val, lowercase, separator)

        normalized[new_key] = val

    return normalized


def compress_and_sort_by_occurence(container, reverse=True, values_only=True):
    """
    Returns distinct elements sorted by the number of their
    occurence in `container`.
    Useful when it is necessary to push something relevant
    to the top (e.g. distinct topics from the list of topics).

    :param container: <list> or <tuple> whose elements are <str>
    :param reverse: <bool>
    :param values_only: <bool> if True, returns list of keys,
                               otherwise, returns list of dicts
                               with number of occurences.
    :return: <list>
    """
    aggregated = {}
    for elm in container:
        try:
            aggregated[elm] += 1
        except KeyError:
            aggregated[elm] = 1

    aggregated = [{'elm': t, 'num': n} for t, n in aggregated.items()]
    aggregated = sorted(aggregated, key=lambda x: x['num'], reverse=reverse)

    if values_only:
        return [x['elm'] for x in aggregated]

    return aggregated
