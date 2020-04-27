#!/usr/bin/env python

import argparse
import time

from lib.config import read_config
from lib.log import set_log_level, debug
from lib.routers import get_lte_nodes
from lib.stats import collect_stats, calculate_total
from lib.units import bytes_to_human
from lib.webpage import create_html_document


def parse_arguments():
    """Get commandline arguments."""
    parser = argparse.ArgumentParser(
        description='Retrieve LTE quota stats and generate html document.')
    parser.add_argument('--config', '-c', help='config file',
                        default='/etc/128technology/lte_quota_info.json')
    parser.add_argument('--debug', '-d', action='store_true',
                        help='show debug messages')
    return parser.parse_args()


def main():
    args = parse_arguments()
    log_level = 'INFO'
    if args.debug:
        log_level = 'DEBUG'
    set_log_level(log_level)

    config = read_config(args.config)
    node_stats = []
    for node_info in get_lte_nodes(config):
        router_name = node_info['router']
        node_name = node_info['node']
        quota = node_info['quota']

        stats_log = collect_stats(config, node_info)
        if not stats_log:
            debug('No result for router:', router_name, 'node:', node_name)
            continue
        total = calculate_total(stats_log)
        percentage = total * 100 / quota

        # coloring progress bar
        color = 'bg-success'
        if percentage > config.get('percentage_orange', 80):
            color = 'bg-warning'
        if percentage > config.get('percentage_red', 95):
            color = 'bg-danger'

        node_stats.append({
            'router_name': router_name,
            'node_name': node_name,
            'initial_string': bytes_to_human(quota, html=True),
            'used_string': bytes_to_human(total, html=True),
            'percentage': percentage,
            'color': color,
            'timestamp_unixtime': int(time.time())
        })
    debug(node_stats)
    create_html_document(config, node_stats)


if __name__ == '__main__':
    main()
