"""Unifi implementation."""

from aiohttp import client_exceptions

from .clients import Clients, URL as client_url
from .devices import Devices, URL as device_url
from .errors import raise_error, ResponseError, RequestError


class Controller:
    """Control a UniFi controller."""

    def __init__(self, host, websession, *,
                 username, password, port=8443, site='default'):
        self.host = host
        self.session = websession
        self.port = port
        self.username = username
        self.password = password
        self.site = site

        self.clients = None
        self.devices = None

    async def login(self):
        url = 'login'
        auth = {
            'username': self.username,
            'password': self.password,
            'remember': True,
        }
        await self.request('post', url, json=auth)

    async def sites(self):
        url = 'self/sites'
        sites = await self.request('get', url)
        return {site['desc']: site for site in sites}

    async def initialize(self):
        clients = await self.request('get', client_url)
        self.clients = Clients(clients, self.request)
        devices = await self.request('get', device_url)
        self.devices = Devices(devices, self.request)

    async def request(self, method, path, json=None):
        """Make a request to the API."""
        url = 'https://{}:{}/api/'.format(self.host, self.port)
        url += path.format(site=self.site)

        try:
            async with self.session.request(method, url, json=json) as res:
                if res.content_type != 'application/json':
                    raise ResponseError(
                        'Invalid content type: {}'.format(res.content_type))
                response = await res.json()
                _raise_on_error(response)
                return response['data']

        except client_exceptions.ClientError as err:
            raise RequestError(
                'Error requesting data from {}: {}'.format(self.host, err)
            ) from None


def _raise_on_error(data):
    """Check response for error message."""
    if isinstance(data, dict) and data['meta']['rc'] == 'error':
        raise_error(data['meta']['msg'])
