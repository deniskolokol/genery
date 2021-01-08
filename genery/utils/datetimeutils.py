# -*- coding: utf-8 -*-

"""Operations with dates and timestamps."""


import datetime
import calendar
from math import isclose


def make_tz_aware(dt, tz=datetime.timezone.utc):
    if isinstance(tz, str):
        pass
    dt.replace(tzinfo=tz)
    return dt


def datetime_to_timestamp(dt):
    """Converts datetime.datetime to timestamp."""
    return calendar.timegm(dt.timetuple()) * 1000


def round_datetime_interval(start, end):
    """
    Rounds up a datetime interval to one of the closest time interval
    from the scope. Returns suggested start and end timestamps, e.g.
    [01:05, 20:50] will be rounded to [01:00, 21:00] with the interval
    equal to 10 minutes.

    :param start: <datetime.datetime> start date.
    :param end: <datetime.datetime> end date.
    :return: <int> interval: (ms)
             <int> suggested_start: (timestamp)
             <int> suggested_end: (timestamp)
    """
    if not start or not end:
        return 1800000, None, None

    # Approximate number of bars.
    bars = 50

    supported_intervals = [ # In seconds.
        60,         # 1 minute
        120,        # 2 minutes
        300,        # 5 minutes
        600,        # 10 minutes
        1800,       # 30 minutes
        3600,       # 1 hour
        7200,       # 2 hour
        21600,      # 6 hour
        43200,      # 12 hour
        86400,      # 1 day. Use 00:00 of each 1 day.
        259200,     # 3 days. Use 00:00 of each 3 day.
        604800,     # 1 week. Use 00:00 of each Monday.
        1209600,    # 2 weeks. Use 00:00 of Monday of each 2 weeks.
        2592000,    # 1 month. Use 00:00 of Monday of each 2 weeks.
        7776000,    # 3 months. Use XX/01 00:00 of each month.
        15552000,   # 6 months. Use XX/01 00:00 of each 6 month.
        31104000    # 1 year. Use 01/01/XXXX 00:00 of each year.
    ]
    # Convert dates.
    start = datetime_to_timestamp(start)
    end = datetime_to_timestamp(end)

    # Get difference between two dates.
    delta = (end - start) / 1000 # In secs.

    # Current interval for default bars count.
    base_interval = delta / bars

    # Choose closest interval to current delta.
    interval_index = 0
    delta_interval_difference = None
    for index, interval in enumerate(supported_intervals):
        diff = abs(base_interval - interval)
        if not delta_interval_difference:
            delta_interval_difference = diff
        else:
            if diff < delta_interval_difference:
                interval_index = index

    interval = supported_intervals[interval_index] * 1000 # In ms.

    # Round down start datetime.
    suggested_start = start // interval * interval

    # Round down end datetime.
    if end % interval > 0:
        suggested_end = (end//interval + 1) * interval
    else:
        suggested_end = end

    return interval, suggested_start, suggested_end


def human_readable_time(ms, round_to=3):
    """
    A very crude function for human readable time:
    - anything shorter than millisec is instant
    - everything longer than hours are days.
    """
    if ms < 0:
        raise Exception("Time value cannot be negative!")

    if isclose(ms, 0, abs_tol=1e-01):
        return "instantly"

    patt = "{:." + str(round_to) + "f}"
    if ms < 1000:
        patt += " ms"
        return patt.format(ms)

    interval = ms / 1000
    if 60 > interval >= 1:
        patt += " sec"
        return patt.format(interval)

    interval = interval / 60
    if 60 > interval >= 1:
        patt += " min"
        return patt.format(interval)

    interval = interval / 60
    if 24 > interval >= 1:
        patt += " hr"
        return patt.format(interval)

    interval = interval / 24
    if isclose(interval, 1, abs_tol=1e-01):
        patt += " day"
    else:
        patt += " days"
    return patt.format(interval)
