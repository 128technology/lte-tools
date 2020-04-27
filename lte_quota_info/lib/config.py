"""Module for config file handling."""
import json


def read_config(filename):
    """Read a config file in yaml format."""
    with open(filename) as fd:
        return json.load(fd)
