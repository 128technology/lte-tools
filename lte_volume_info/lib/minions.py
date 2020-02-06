"""Provide generic functions for salt minions."""

import json


def call_minion_cmd(node, cmd):
    """Call a command on a minion and return output."""
    content = {}
    try:
        import salt.client
        local = salt.client.LocalClient('/etc/128technology/salt/master')
        ret = local.cmd(node, 'cmd.run', [cmd], timeout=3)
        if not ret:
            content = {'error': 'Could not connect to router node'}
        else:
            content = ret[node]
            if content is False:
                content = {'error': 'Could not connect to router node'}
    except ImportError:
        content = {'error': 'Could not load module "salt.client"'}
    return content
