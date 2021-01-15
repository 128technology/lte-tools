#!/usr/bin/env python3

import argparse
import json
import os
import requests
import sys
import time

from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

CACHE_TIMEOUT = 30  # in seconds
CACHE_FILE = '/var/run/128technology/snmp_lte_stats.cache'
BASE = '.1.3.6.1.4.1.45956.1.'
STATS = (
    'Radio Interface',
    'RSSI Signal Strength',
    'Signal Strength',
    'Active Band Class',
    'Active Channel',
    'Carrier',
    'Connection Status',
    'Enabled LTE Bands',
    'RSRP Signal Strength',
    'RSRQ Signal Strength',
    'SNR Signal Strength',
)
TYPES = {
    'RSSI Signal Strength' : 'integer',
}
NETWORK_TYPES = ('none', 'gsm', 'umts', 'lte')


def parse_arguments():
    """Get commandline arguments."""
    parser = argparse.ArgumentParser(
        description='Provide LTE stats through SNMP')
    parser.add_argument('oid', help='the OID')
    parser.add_argument('-g', '--get', help='get value', action='store_true')
    parser.add_argument('-n',  '--next', help='get next value', action='store_true')
    return parser.parse_args()


def error(*msg):
    print(*msg)
    sys.exit(1)


def post(location, json, token='', host='localhost'):
    url = 'https://{}/{}'.format(host, location.strip('/'))
    headers = {
        'Content-Type': 'application/json',
    }
    if token:
        headers['Authorization'] = 'Bearer {}'.format(token)
    request = requests.post(
        url, headers=headers, json=json,
        verify=False)
    return request


def login(user='admin'):
    key_content = ''
    with open('/home/admin/.ssh/pdc_ssh_key') as fd:
        key_content = fd.read()
    json = {
        'username': user,
        'local': key_content
    }
    request = post('/api/v1/login', json)
    if request.status_code == 200:
        token = request.json()['token']
        return token
    else:
        error('Login has failed.')


def read_cache():
    try:
        timestamp = os.stat(CACHE_FILE).st_mtime
        now = time.time()
        if now - timestamp > CACHE_TIMEOUT:
            # cache has expired
            return {}

        with open(CACHE_FILE) as fd:
            lte_stats = json.load(fd)
            return lte_stats

    except FileNotFoundError:
        return {}


def write_cache(lte_stats):
    with open(CACHE_FILE, 'w') as fd:
        json.dump(lte_stats, fd)


def lte_stats(token, interface='LTE1'):
    json = {
        'query': '{ allRouters { nodes { nodes { nodes { deviceInterfaces(name: "' + interface + '") { nodes { networkInterfaces { nodes { deviceInterface { state { networkPluginState } } } } } } } } } } }'
    }
    request = post('/api/v1/graphql', json, token)
    if request.status_code == 200:
        return request.json()['data']['allRouters']['nodes'][0]['nodes']['nodes'][0]['deviceInterfaces']['nodes'][0]['networkInterfaces']['nodes'][0]['deviceInterface']['state']['networkPluginState']['LTE']
    else:
        error('Fetching LET stats has failed.')


def generate_object(index, key, value, type='string'):
    return {
        '100.1.{}.1'.format(index): ['string', key],
        '100.1.{}.2'.format(index): [type, value],
    }


def populate_objects():
    stats = read_cache()
    if not stats:
        token = login()
        stats = lte_stats(token)
        write_cache(stats)
    objects = {}
    i = 1
    for stat in STATS:
        if stat in stats:
            value = stats[stat]
            type = TYPES.get(stat, 'string')
            if value.endswith(' dBm'):
                type = 'integer'
                value = value.strip(' dBm')
            objects.update(generate_object(i, stat, value, type))
            if stat == 'Radio Interface':
                i += 1
                try:
                    network_type = NETWORK_TYPES.index(value)
                except ValueError:
                    network_type = -1
                objects.update(
                    generate_object(i, 'Network Type', str(network_type), 'integer'))
        i += 1
    return objects


if __name__ == '__main__':
    args = parse_arguments()
    objects = populate_objects()
    if args.get:
        if args.oid.startswith(BASE):
            key = args.oid.split(BASE)[1]
            obj = objects.get(key)
            if obj:
                 print('\n'.join([args.oid] + obj))
