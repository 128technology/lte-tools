#!/usr/bin/env python

from __future__ import print_function
import argparse
import json
import os
import requests
import sys
from jinja2 import Template
from xml.etree import ElementTree

from providers import providers

# $ cp 128t_black.png /var/www/128technology/


TEMPLATE = 'lte_volume_info.template'


def parse_arguments():
    """Get commandline arguments."""
    parser = argparse.ArgumentParser(
        description='Retrieve LTE volume stats and generate html document.')
    parser.add_argument('--cache-dir', help='path to stats cache',
                        default='/run/128technology/lte_volume_info_cache')
    parser.add_argument('--html-path', help='path to html document',
                        default='/var/www/128technology/lte_volume_info.html')
    parser.add_argument('--config-path', help='path to 128T config',
                        default='/var/lib/128technology/t128-running.xml')
    parser.add_argument('--percentage-orange', default=80, type=int,
                        help='show bar as orange if percentage > X')
    parser.add_argument('--percentage-red', default=95, type=int,
                        help='show bar as red if percentage > X')
    return parser.parse_args()


def get_lte_nodes(config_path):
    """Get LTE routers connected to conductor."""
    nodes = []
    tree = ElementTree.parse(config_path)
    ns = {'sys': 'http://128technology.com/t128/config/system-config'}
    root = tree.getroot()
    for node in root.findall('.//sys:node', ns):
        node_name = node.find('sys:name', ns).text
        for device_interface in node.findall('sys:device-interface', ns):
            type = device_interface.find('sys:type', ns)
            device_name = device_interface.find('sys:name', ns).text
            if type is None:
                # ignore unspecified device type
                continue
            device_type = type.text
            if device_type == 'lte':
                # populate lte_node_config
                node_config = {
                    'node_name': node_name,
                    'device_name': device_name,
                    'asset_id': None,
                    'apn': None
                }
                node_config['asset_id'] = node.find('sys:asset-id', ns).text
                try:
                    lte = device_interface.find('sys:lte', ns)
                    node_config['apn'] = lte.find('sys:apn-name', ns).text
                except AttributeError:
                    pass
                nodes.append(node_config)
    return nodes


def cache_node_stats(cache_dir, stats):
    """Write node stats to cache_dir."""
    try:
        os.makedirs(cache_dir)
    except OSError:
        # ignore if cache_dir already exists
        pass
    try:
        cache_file = os.path.join(cache_dir, stats['node_name'] + '.json')
        with open(cache_file, 'w') as fd:
            json.dump(stats, fd)
    except:
        # ignore if file cannot be created
        pass


def create_html_document(node_stats, html_path):
    """Create html document based on stats."""
    try:
        TEMPLATE_PATH = os.path.join(sys.path[0], TEMPLATE)
        with open(TEMPLATE_PATH, 'r') as fd:
            template = Template(fd.read())
        with open(html_path, 'w') as fd:
            fd.write(template.render(node_stats=node_stats))
    except:
        raise


def main():
    """The main loop."""
    args = parse_arguments()

    # populate APN specific function references
    apn_get_stats = {}
    for provider in providers:
        for apn in provider.get_apns():
            apn_get_stats[apn] = provider.get_stats

    # mock data for demo purposes
    mock_file = os.path.join(sys.path[0], 'mocked_node_stats.json')
    if os.path.isfile(mock_file):
        with open(mock_file) as fd:
            node_stats = json.load(fd)
    else:
        # retrieve volume stats for all nodes with LTE device
        node_stats = []
        for node_info in get_lte_nodes(args.config_path):
            node_name = node_info['node_name']
            stats = {'node_name': node_name}
            apn = node_info['apn']
            if apn not in apn_get_stats:
                stats['error'] = 'APN is not supported: {}'.format(apn)
            else:
                stats.update(apn_get_stats[apn](node_info['asset_id']))
                if 'error' not in stats:
                    # coloring progress bar
                    stats['color'] = 'bg-success'
                    if stats['percentage'] > args.percentage_orange:
                        stats['color'] = 'bg-warning'
                    if stats['percentage'] > args.percentage_red:
                        stats['color'] = 'bg-danger'
            node_stats.append(stats)
            cache_node_stats(args.cache_dir, stats)

    # generate combined html file for all nodes
    create_html_document(node_stats, args.html_path)


if __name__ == '__main__':
    main()
