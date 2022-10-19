
"""
Async DRACOON config adapter based on httpx, tqdm and pydantic
V1.6.0
(c) Octavio Simone, October 2022 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/config
Please note: maximum 500 items are returned in GET requests

"""


import logging

import httpx

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.config.responses import AlgorithmVersionInfoList, ClassificationPoliciesConfig, GeneralSettingsInfo, InfrastructureProperties, PasswordPoliciesConfig, ProductPackageResponseList, S3TagList, SystemDefaults
from dracoon.errors import ClientDisconnectedError, InvalidClientError


class DRACOONConfig:

    """
    API wrapper for DRACOON config endpoint:
    Config endpoints returning policies, infrastructure, defaults 
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.config')
        
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/config/info'
    
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

            self.logger.debug("DRACOON config adapter created.")
        
        else:
            self.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
        
    async def get_system_defaults(self, raise_on_err: bool = False) -> SystemDefaults:
        
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/defaults'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting system defaults failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved system defaults.")
        return SystemDefaults(**res.json())
    
    async def get_general_settings(self, raise_on_err: bool = False) -> GeneralSettingsInfo:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/general'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting general settings failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved general settings.")
        return GeneralSettingsInfo(**res.json())
    
    async def get_infrastructure_properties(self, raise_on_err: bool = False) -> InfrastructureProperties:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/infrastructure'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting infrastructure properties failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved infrastructure properties.")
        return InfrastructureProperties(**res.json())
    
    async def get_algorithms(self, raise_on_err: bool = False) -> AlgorithmVersionInfoList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/algorithms'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting infrastructure properties failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved infrastructure properties.")
        return AlgorithmVersionInfoList(**res.json())
    
    async def get_classification_policies(self, raise_on_err: bool = False) -> ClassificationPoliciesConfig:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/classifications'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting infrastructure properties failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved infrastructure properties.")
        return ClassificationPoliciesConfig(**res.json())
    
    async def get_password_policies(self, raise_on_err: bool = False) -> PasswordPoliciesConfig:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/passwords'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting password policies failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved password policies.")
        return PasswordPoliciesConfig(**res.json())
        
    async def get_product_packages(self, raise_on_err: bool = False) -> ProductPackageResponseList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/product_packages'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting product packages failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved product packages.")
        return ProductPackageResponseList(**res.json())
    
    async def get_current_product_package(self, raise_on_err: bool = False) -> ProductPackageResponseList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/product_packages/current'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting current product package failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved current product package.")
        return ProductPackageResponseList(**res.json())
    
    async def get_s3_tags(self, raise_on_err: bool = False) -> S3TagList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/s3_tags'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting s3 tags failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved s3 tags.")
        return S3TagList(**res.json())