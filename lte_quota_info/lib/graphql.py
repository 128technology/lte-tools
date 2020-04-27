"""Handle GraphQL connections."""
import requests


def extract(data, find_key):
    if type(data) == list:
        # descent to first element in list
        return extract(data[0], find_key)
    if type(data) == dict:
        if find_key in data:
            return data[find_key]
        for key, value in data.items():
            # descent to first element in dictionary
            return extract(value, find_key)


class GraphQL:
    """Representation of GraphQL connection."""

    def __init__(self, api_key, host='localhost'):
        """Constructor - loading credentials."""
        self.host = host
        self.api_key = api_key

    def query(self, query):
        """Query data per GraphQL."""
        headers = {
            'Content-Type': 'application/json',
            'Authorization': 'Bearer {}'.format(self.api_key),
        }
        url = 'https://{}/api/v1/graphql'.format(self.host)
        request = requests.post(
            url, headers=headers, json={'query': query}, verify=False)
        if request.status_code == 200:
            return request.json()
        else:
            raise Exception(
                "Query failed to run by returning code of {}. {}".format(
                    request.status_code, query))
