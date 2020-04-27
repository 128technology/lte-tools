"""Handle routers, nodes, interfaces."""
from lib.log import debug, fatal
from lib.restapi import RestApi
from lib.units import human_to_size


def get_lte_nodes(config):
    """Get LTE routers connected to conductor."""
    INTERFACE_TYPE = 'lte'
    nodes = []
    api_key = config.get('api_key')
    if not api_key:
        fatal('No api_key has been specified in config file.')
    quotas = config.get('quotas')
    default_quota = config.get('default_quota', human_to_size('5 GB'))
    conductor = config.get('conductor', 'localhost')

    api = RestApi(api_key, host=conductor)
    for router in api.get_routers():
        router = router['name']
        for node in api.get_nodes(router):
            node = node['name']
            if '-conductor' in node:
                continue
            if not api.node_is_deployed(router, node):
                continue

            for device_interface in api.get_device_interfaces(router, node):
                if device_interface.get('type') == INTERFACE_TYPE:
                    quota = human_to_size(quotas.get(router))
                    if not quota:
                        quota = default_quota

                    # populate lte_node_config
                    node_config = {
                        'router': router,
                        'node': node,
                        'interface': device_interface.get('name'),
                        'quota': quota,
                    }
                    debug(node_config)
                    nodes.append(node_config)
    return nodes
