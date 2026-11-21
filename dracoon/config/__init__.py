
"""
Async DRACOON config adapter based on httpx, tqdm and pydantic
V1.6.0
(c) Octavio Simone, October 2022 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/config
Please note: maximum 500 items are returned in GET requests

"""

from typing import Optional
import logging

from dracoon.client import DRACOONClient
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
  
        else:
            self.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
    
    async def get_system_defaults(self, raise_on_err: bool = False) -> Optional[SystemDefaults]:
        
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/defaults'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting system defaults failed.")
            return None
        
        self.logger.info("Retrieved system defaults.")
        return SystemDefaults(**res.json())
    
    async def get_general_settings(self, raise_on_err: bool = False) -> Optional[GeneralSettingsInfo]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/general'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting general settings failed.")
            return None
        
        self.logger.info("Retrieved general settings.")
        return GeneralSettingsInfo(**res.json())
    
    async def get_infrastructure_properties(self, raise_on_err: bool = False) -> Optional[InfrastructureProperties]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/infrastructure'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting infrastructure properties failed.")
            return None
        
        self.logger.info("Retrieved infrastructure properties.")
        return InfrastructureProperties(**res.json())
    
    async def get_algorithms(self, raise_on_err: bool = False) -> Optional[AlgorithmVersionInfoList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/algorithms'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting infrastructure properties failed.")
            return None
        
        self.logger.info("Retrieved infrastructure properties.")
        return AlgorithmVersionInfoList(**res.json())
    
    async def get_classification_policies(self, raise_on_err: bool = False) -> Optional[ClassificationPoliciesConfig]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/classifications'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting infrastructure properties failed.")
            return None
        
        self.logger.info("Retrieved infrastructure properties.")
        return ClassificationPoliciesConfig(**res.json())
    
    async def get_password_policies(self, raise_on_err: bool = False) -> Optional[PasswordPoliciesConfig]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/policies/passwords'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting password policies failed.")
            return None
        
        self.logger.info("Retrieved password policies.")
        return PasswordPoliciesConfig(**res.json())
    
    async def get_product_packages(self, raise_on_err: bool = False) -> Optional[ProductPackageResponseList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/product_packages'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting product packages failed.")
            return None
        
        self.logger.info("Retrieved product packages.")
        return ProductPackageResponseList(**res.json())
    
    async def get_current_product_package(self, raise_on_err: bool = False) -> Optional[ProductPackageResponseList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/product_packages/current'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting current product package failed.")
            return None
        
        self.logger.info("Retrieved current product package.")
        return ProductPackageResponseList(**res.json())
    
    async def get_s3_tags(self, raise_on_err: bool = False) -> Optional[S3TagList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/s3_tags'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting s3 tags failed.")
            return None
        
        self.logger.info("Retrieved s3 tags.")
        return S3TagList(**res.json())