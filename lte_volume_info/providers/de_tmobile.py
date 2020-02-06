"""LTE volume stats module for T-Mobile Germany."""
import json
from time import gmtime, strftime
from lib import minions

# API_URL = 'http://pass.telekom.de/api/service/generic/v1/status'
API_URL = 'http://109.237.176.33/api/service/generic/v1/status'
CURL_CMD = 'curl -sS --connect-timeout 2 --user-agent "Mozilla/4.0" ' + API_URL


def get_apns():
    """Return APNs."""
    return ('internet.telekom', 'internet.t-mobile', 'internet.t-d1')


def extract_used_volume(data):
    """Extract used and initial volume."""
    stats = {}
    stats['used_bytes'] = data.get('usedVolume')
    stats['used_string'] = data.get('usedVolumeStr')
    stats['initial_bytes'] = data.get('initialVolume')
    stats['initial_string'] = data.get('initialVolumeStr')
    stats['percentage'] = data.get('usedPercentage')
    stats['timestamp_unixtime'] = data.get('usedAt') / 1000
    stats['timestamp_utc'] = strftime(
        '%Y-%m-%d %H:%M:%S UTC', gmtime(stats['timestamp_unixtime']))
    return stats


def get_stats(asset_id):
    """Return stats about initial and used volume."""
    stats = {}
    content = minions.call_minion_cmd(asset_id, CURL_CMD)
    if 'Connection timed out' in content:
        stats = {'error': 'Connection to API service timed out.'}
    elif 'error' in content:
        stats = {'error': content['error']}
    elif 'you need an internet connection over the mobile network.' in content:
        stats = {
            'error': 'API service at pass.telekom.de requires LTE connection.'}
    else:
        try:
            data = json.loads(content.decode('utf8').replace(u'\xa0', u' '))
            stats = extract_used_volume(data)
        except ValueError:
            stats = {'error': 'Error retrieving volume stats'}
    return stats
