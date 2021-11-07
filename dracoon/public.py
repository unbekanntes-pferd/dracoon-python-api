"""
Async DRACOON public adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for public endpoints
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/public

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""

import httpx
from .core import DRACOONClient, OAuth2ConnectionType


class DRACOONPublic:

    """
    API wrapper for DRACOON nodes endpoint:
    Node operations (rooms, files, folders), room webhooks, comments and file transfer (up- and download)
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/public/system/info'
        else:
            raise ValueError(
                'DRACOON client must be connected: client.connect()')

    async def get_system_info(self):
        """ get sytem information (S3) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.get(self.api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    async def get_auth_ad_info(self):
        """ get active directory information """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/auth/ad'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    async def get_auth_openid_info(self):
        """ get openid information """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/auth/openid'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res




