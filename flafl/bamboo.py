import netrc
import requests


class BambooConnection:
    """Create connection to Atlassian tool, for API calls"""

    def __init__(self, netrc_file, hostname):
        """Create the connection, using the provided netrc file"""
        netrc_object = netrc.netrc(netrc_file)
        username = netrc_object.authenticators(hostname)[0]
        password = netrc_object.authenticators(hostname)[2]
        self.auth = (username, password)
        self.url = "https://" + hostname + "/rest/api"

    def get(self, resource, apiversion="latest"):
        """Issue a GET API call"""
        response = requests.get(
            url=self.url + "/" + apiversion + "/" + resource, auth=self.auth
        )
        return response

    def post(self, resource, apiversion="latest", json=None):
        """Issue a POST API call with a JSON payload"""
        response = requests.post(
            url=self.url + "/" + apiversion + "/" + resource, auth=self.auth, json=json
        )
        return response
