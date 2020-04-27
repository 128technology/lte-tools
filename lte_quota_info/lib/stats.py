"""Handle stats file read/write and stats retrieval."""
import json
import os
import time

from lib.log import debug, fatal, warn
from lib.graphql import GraphQL, extract


def get_unix_timestamp():
    return int(time.time())


def cleanup_stats(stats_dir, days):
    """Remove files older than n days."""
    now = get_unix_timestamp()
    max_age = days * 86400
    for file in os.listdir(stats_dir):
        path = os.path.join(stats_dir, file)
        statinfo = os.stat(path)
        age = now - statinfo.st_mtime
        if age > max_age:
            debug('Deleting old file:', path, '({} days old)'.format(
                int(age / 86400)))
            os.unlink(path)


def read_stats(filename):
    """Read stats file."""
    try:
        with open(filename) as fd:
            return json.load(fd)
    except:
        warn('Cannot load stats file: {}'.format(filename))
        return []


def write_stats(stats, filename):
    """Write stats file."""
    try:
        with open(filename, 'w') as fd:
            json.dump(stats, fd)
    except:
        fatal('Cannot write stats file: {}'.format(filename))


def collect_stats(config, node_info):
    """Collect stats and update files."""
    router = node_info['router']
    node = node_info['node']
    interface = node_info['interface']

    api_key = config.get('api_key')
    if not api_key:
        fatal('No api_key has been specified in config file.')

    # create stats_dir if missing
    stats_dir = config.get(
        'stats_dir', '/var/lib/128technology/lte_qouta_info')
    if stats_dir and not os.path.isdir(stats_dir):
        os.mkdir(stats_dir)
    else:
        cleanup_stats(stats_dir, config.get('retention_days', 60))

    conductor = config.get('conductor', 'localhost')
    stats = [int(time.time())]
    # Get current kpi for received/sent via GraphQL
    # (values during last 10 seconds interval)
    query = '''{ metrics { interface { %(kpi)s {
        bytes(router: "%(router)s", node: "%(node)s", port: "%(interface)s") {
          timeseries(startTime: "now-10") { timestamp value } } } } } }'''
    graphql = GraphQL(api_key, host=conductor)
    for kpi in ('received', 'sent'):
        result = graphql.query(query % locals())
        try:
            value = int(extract(result, 'value'))
        except TypeError:
            return None
        stats.append(value)

    stats_file = os.path.join(
        stats_dir,
        'lte_quota_info_{}_{}_{}_{}.stats'.format(
            router, node, interface, time.strftime('%Y-%m')))
    stats_log = read_stats(stats_file)
    stats_log.append(stats)
    write_stats(stats_log, stats_file)
    return stats_log


def calculate_total(stats_log):
    """Based on the logged stats calculate monthly totals."""
    buckets = []
    first_received = None
    first_sent = None
    for entry in stats_log:
        current_received = entry[1]
        current_sent = entry[2]

        # handle first entry for a new bucket
        if not first_received:
            first_received = current_received
            received = current_received
        if not first_sent:
            first_sent = current_sent
            sent = current_sent

        # handle integer overflows/restarts
        if current_received < received:
            buckets.append(received - first_received)
            first_received = current_received
        if current_sent < sent:
            buckets.append(sent - first_sent)
            first_sent = current_sent

        # store current values to last
        received = current_received
        sent = current_sent

    buckets.append(received - first_received)
    buckets.append(sent - first_sent)
    total = sum(buckets)
    debug('buckets:', buckets, 'total:', total)
    return total
