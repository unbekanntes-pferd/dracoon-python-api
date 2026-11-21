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
from typing import Optional
import logging

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
  
    @property
    def branding(self) -> DRACOONPublicBranding:
        return DRACOONPublicBranding(dracoon_client=self.dracoon)

    async def get_system_info(self, raise_on_err: bool = False) -> Optional[SystemInfo]:
        """ get sytem information (S3) """

        if self.raise_on_err:
            raise_on_err = True

        res = await self.dracoon.request('GET', self.api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting system info failed.")
            return None
        
        self.logger.info("Retrieved system info.")
        return SystemInfo(**res.json())
    
    async def get_auth_ad_info(self, raise_on_err: bool = False) -> Optional[AuthADInfoList]:
        """ get active directory information """

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + '/auth/ad'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting AD auth info failed.")
            return None
        self.logger.info("Retrieved AD auth info.")
        return AuthADInfoList(**res.json())
    
    async def get_auth_openid_info(self, raise_on_err: bool = False) -> Optional[AuthOIDCInfoList]:
        """ get openid information """
        
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + '/auth/openid'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting AD auth info failed.")
            return None
        
        self.logger.info("Retrieved OIDC auth info.")
        return AuthOIDCInfoList(**res.json())