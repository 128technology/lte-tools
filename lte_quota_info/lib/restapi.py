"""Handle Rest API connections."""
from lib.log import fatal

import requests
urllib3 = requests.packages.urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)


class RestApi:
    """Representation of REST connection."""

    def __init__(self, api_key, host='localhost'):
        """Constructor - loading credentials."""
        self.api_key = api_key
        self.host = host

    def get(self, location):
        """Get data per REST API."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_key),
        }
        url = 'https://{}/api/v1{}'.format(self.host, location)
        try:
            response = requests.get(url, headers=headers, verify=False)
            response.raise_for_status()
        except requests.exceptions.HTTPError:
            fatal('REST API credentials are invalid.')
        return response

    def get_routers(self):
        return self.get('/router').json()

    def get_nodes(self, router):
        return self.get('/config/running/authority/router/{}/node'.format(
            router)).json()

    def node_is_deployed(self, router, node):
        location = '/config/running/authority/router/{}/node/{}'.format(
            router,
            node,
        )
        if self.get(location).json()['asset-id']:
            return True
        return False

    def get_device_interfaces(self, router, node):
        return self.get(('/config/running/authority/router/{}/node/{}'
                         '/device-interface').format(router, node)).json()

    def get_lan_ip_address(self, router, node, interface):
        first_network_interface = self.get((
            '/config/running/authority/router/{}/node/{}'
            '/device-interface/{}/network-interface').format(
                router, node, interface)).json()[0]['name']

        return self.get((
            '/config/running/authority/router/{}/node/{}'
            '/device-interface/{}/network-interface/{}/address').format(
                router, node, interface, first_network_interface)).json()[0]['ip-address']
