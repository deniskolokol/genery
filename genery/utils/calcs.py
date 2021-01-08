# -*- coding: utf-8 -*-

"""Calculations (re-scaling, etc.)"""


from math import ceil


def rescale(data, maximum):
    """
    Crude and simple rescaling of the numeric values
    of `data` to the maximum number `maximum`.

    :param data: <dict> in the form of {key: val <float> or <int>}
    :return: <dict> if the same structure.
    """
    total = float(sum(data.values()))
    if total <= 0.:
        return data

    conv = lambda x: ceil(x) if isinstance(maximum, int) else x
    scaled = []
    for key, val in data.items():
        scaled.append({'key': key, 'val': conv(val / total * maximum)})

    # Adjust resulting total to maximum integer
    # (.ceil can raise it a little).
    if isinstance(maximum, int):
        scaled = sorted(scaled, key=lambda x: x['val'])
        scaled_size = len(scaled)
        i = 0
        while (sum(x['val'] for x in scaled) > maximum) and (i < scaled_size):
            new_val = max(0, scaled[i]['val']-1)
            scaled[i]['val'] = new_val
            i += 1

    return dict((x['key'], x['val']) for x in scaled)
