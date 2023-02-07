#!/usr/bin/env python3

import argparse
import json
import os
import pathlib
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


class UnauthorizedException(Exception):
    pass

class RestGraphqlApi(object):
    """Representation of REST connection."""

    token = None
    authorized = False
    headers = {
        'Content-Type': 'application/json',
    }

    def __init__(self, host='localhost', verify=False, user='admin', password=None, app=__file__):
        self.host = host
        self.verify = verify
        self.user = user
        self.password = password
        basename = os.path.basename(app).split('.')[0]
        self.user_agent = basename
        self.token_file = os.path.join(
             pathlib.Path.home(), '.{}.token'.format(basename))
        self.read_token()
        self.headers.update({
             'User-Agent': self.user_agent,
             'Authorization': f'Bearer {self.token}',
        })

        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.hooks['response'].append(self.refresh_token)

    def read_token(self):
        try:
            with open(self.token_file) as fd:
                self.token = fd.read()
        except FileNotFoundError:
            pass

    def write_token(self):
        try:
            with open(self.token_file, 'w') as fd:
                fd.write(self.token)
        except:
            raise

    def refresh_token(self, r, *args, **kwargs):
        if r.status_code == 401:
            token = self.login()
            self.session.headers.update({'Authorization': f'Bearer {token}'})
            r.request.headers['Authorization'] = self.session.headers['Authorization']
            return self.session.send(r.request, verify=self.verify)

    def post(self, location, json, authorization_required=True):
        """Send data per REST API via post."""
        url = 'https://{}/api/v1/{}'.format(self.host, location.strip('/'))
        request = self.session.post(url, json=json, verify=self.verify)
        return request

    def login(self):
        json = {
            'username': self.user,
        }
        if self.password:
            json['password'] = self.password
        else:
            key_file = 'pdc_ssh_key'
            if not os.path.isfile(key_file):
                key_file = '/home/admin/.ssh/pdc_ssh_key'

            key_content = ''
            with open(key_file) as fd:
                key_content = fd.read()
            json['local'] = key_content
        request = self.post('/login', json, authorization_required=False)
        if request.status_code == 200:
            self.token = request.json()['token']
            self.write_token()
            return self.token
        else:
            message = request.json()['message']
            raise UnauthorizedException(message)


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


def lte_stats(api, interface='LTE1'):
    json = {
        'query': '{ allRouters { nodes { nodes { nodes { deviceInterfaces(name: "' + interface + '") { nodes { networkInterfaces { nodes { deviceInterface { state { networkPluginState } } } } } } } } } } }'
    }
    request = api.post('/graphql', json)
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
        api = RestGraphqlApi()
        stats = lte_stats(api)
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
            if value.endswith(' dB'):
                type = 'integer'
                value = value.strip(' dB')
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
