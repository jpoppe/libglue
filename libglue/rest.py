"""libGlue REST library."""

__author__ = "Jasper Poppe"
__copyright__ = "Copyright 2012-2022 Jasper Poppe"
__license__ = "MIT"
__status__ = "Development"


from requests import request


class RestApiClient:
    """REST API client."""

    def __init__(self, url: str, headers, verify_ssl: bool = False):
        """Initialize client variables."""
        self.api_url = url
        self.headers = headers
        self.verify_ssl = verify_ssl

    def call(self, endpoint: str, method="GET", parameters=None):
        """Call REST API."""
        method = method.upper()

        response = request(
            method,
            self.api_url + endpoint,
            headers=self.headers,
            data=parameters if parameters and method in ["POST", "PUT"] else None,
            params=parameters if parameters and method in ["GET"] else None,
            timeout=5,
            verify=self.verify_ssl,
        )

        if response.status_code != 200:
            response.raise_for_status()

        return response.json()
