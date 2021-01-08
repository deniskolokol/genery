# -*- coding: utf-8 -*-

import time

from genery.utils import RecordDict


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


def timeit(method):
    """Profiling decorator, measures function runing time."""
    def timeit_wrapper(*args, **kwargs):
        time_started = time.time()
        result = method(*args, **kwargs)
        time_ended = time.time()
        time_sec = time_ended - time_started

        print('{}   {:8.5f} min   {:8.5f} s   {:8.5f} ms'.format(
            method.__name__,
            time_sec / 60,
            time_sec,
            time_sec * 1000))

        return result
    return timeit_wrapper
