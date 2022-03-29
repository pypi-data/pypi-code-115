import collections
import copy
import datetime
import itertools
import typing

import dateutil


def get_effects(obj: dict, relevant: dict, additional: dict = None):
    """
    Splits a LoRa object up into several objects, based on changes in
    specified attributes

    The parameters 'relevant' and 'additional' detail which attributes to split
    on and which additional attributes to include in the objects, respectively.
    Both follow the same structure.

    A dict with the three 'groups' found in LoRa objects as keys, with the
    values being a tuple of the keys of the individual fields. E.g.:

    {
        "relationer": ('enhedstype', 'opgaver')
    }

    :param obj: A LoRa object
    :param relevant: The attributes to split on
    :param additional: Additional attributes to include in the result
    :return:
    """
    chunks = set()

    everything = collections.defaultdict(tuple)

    for group in relevant:
        everything[group] += relevant[group]
    for group in additional or {}:
        everything[group] += additional[group]

    # extract all beginning and end timestamps for all effects
    for group, keys in relevant.items():
        if group not in obj:
            continue

        entries = obj[group]

        for key in keys:
            if key not in entries:
                continue

            for entry in entries[key]:
                chunks.update((
                    _parse_timestamp(entry['virkning']['from']),
                    _parse_timestamp(entry['virkning']['to']),
                ))

    # sort them, and apply the filter, if given
    chunks = get_date_chunks(chunks)

    def filter_list(entries, start, end):
        for entry in entries:
            entry_start = _parse_timestamp(entry['virkning']['from'])
            entry_end = _parse_timestamp(entry['virkning']['to'])

            if entry_start < end and entry_end > start:
                yield entry

    # finally, extract chunks corresponding to each cut-off
    for start, end in chunks:
        effect = {
            group: {
                key: list(filter_list(obj[group][key], start, end))
                for key in everything[group]
                if key in everything[group] and key in obj[group]
            }
            for group in everything
            if group in obj
        }

        if any(k for g in effect.values() for k in g.values()):
            yield start, end, effect


def get_date_chunks(dates):
    """
    Given a list of dates
    :param dates:
    :return:
    """
    a, b = itertools.tee(sorted(dates))

    # drop the first item -- doing a raw next() fails in Python 3.7
    for __ in itertools.islice(b, 1):
        pass

    yield from zip(a, b)


def _parse_timestamp(
    timestamp: typing.Union[datetime.datetime, str]
) -> datetime.datetime:
    if timestamp == 'infinity':
        dt = datetime.datetime.max
    elif timestamp == '-infinity':
        dt = datetime.datetime.min
    elif type(timestamp) == str:
        dt = dateutil.parser.isoparse(timestamp)
    elif type(timestamp) == datetime:
        dt = copy.copy(timestamp)
    else:
        raise TypeError("Invalid parameter {}".format(timestamp))

    if not dt.tzinfo:
        dt = dt.replace(tzinfo=datetime.timezone.utc)

    return dt
