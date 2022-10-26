"""
Async DRACOON public adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for public endpoints
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/public

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""
import logging
import httpx
from dracoon.branding import DRACOONPublicBranding

from dracoon.client import DRACOONClient
from dracoon.errors import InvalidClientError
from .responses import AuthOIDCInfoList, AuthADInfoList, SystemInfo


class DRACOONPublic:

    """
    API wrapper for DRACOON public endpoint:
    Get system info, auth info (AD, OIDC)
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.public')
        
        self.dracoon = dracoon_client
        self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/public/system/info'

        if self.dracoon.raise_on_err:
            self.raise_on_err = True
        else:
            self.raise_on_err = False
        self.logger.debug("DRACOON public adapter created.")
        
    @property
    def branding(self) -> DRACOONPublicBranding:
        return DRACOONPublicBranding(dracoon_client=self.dracoon)


    async def get_system_info(self, raise_on_err: bool = False) -> SystemInfo:
        """ get sytem information (S3) """

        if self.raise_on_err:
            raise_on_err = True

        try:
            res = await self.dracoon.http.get(self.api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting system info failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved system info.")
        return SystemInfo(**res.json())

    async def get_auth_ad_info(self, raise_on_err: bool = False) -> AuthADInfoList:
        """ get active directory information """

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/auth/ad'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting AD auth info failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        self.logger.info("Retrieved AD auth info.")
        return AuthADInfoList(**res.json())

    async def get_auth_openid_info(self, raise_on_err: bool = False) -> AuthOIDCInfoList:
        """ get openid information """
        
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/auth/openid'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting AD auth info failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved OIDC auth info.")
        return AuthOIDCInfoList(**res.json())