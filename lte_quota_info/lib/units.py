"""Handle human readable units."""
from math import log


units = ['Bytes', 'kB', 'MB', 'GB', 'TB', 'PB', 'EB']


def human_to_size(human):
    """Returns bytes for a human readable string."""
    if not human:
        return human
    bytes, unit = human.split(' ')
    power = units.index(unit) * 10
    bytes = int(bytes) * (2 ** power)
    return bytes


def bytes_to_human(bytes, html=False):
    """Returns a human readable string reprentation of bytes."""
    spacer = '&nbsp;' if html else ' '
    for unit in units:
        if bytes < 1024:
            break
        bytes /= 1024
    human = '{}{}{}'.format(bytes, spacer, unit)
    return human
