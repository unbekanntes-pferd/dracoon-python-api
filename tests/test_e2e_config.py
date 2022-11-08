
import os
import asyncio
import unittest
import dotenv
import logging

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.config import DRACOONConfig
from dracoon.config.responses import AlgorithmVersionInfoList, ClassificationPoliciesConfig, GeneralSettingsInfo, InfrastructureProperties, PasswordPoliciesConfig, ProductPackageResponseList, S3TagList, SystemDefaults
from dracoon.errors import HTTPPreconditionsFailedError

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOONConfig(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.config = DRACOONConfig(dracoon_client=self.dracoon)
        self.assertIsInstance(self.config, DRACOONConfig)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_system_defaults(self):
        system_defaults = await self.config.get_system_defaults()
        self.assertIsInstance(system_defaults, SystemDefaults)

    async def test_get_general_settings(self):
        general_settings = await self.config.get_general_settings()
        self.assertIsInstance(general_settings, GeneralSettingsInfo)
    
    async def test_get_infrastructure_properties(self):
        infrastructure_policies = await self.config.get_infrastructure_properties()
        self.assertIsInstance(infrastructure_policies, InfrastructureProperties)
    
    async def test_get_algorithms(self):
        algorithms = await self.config.get_algorithms()
        self.assertIsInstance(algorithms, AlgorithmVersionInfoList)
    
    async def test_get_classification_policies(self):
        classification_policies = await self.config.get_classification_policies()
        self.assertIsInstance(classification_policies, ClassificationPoliciesConfig)
    
    async def test_get_passwords_policies(self):
        password_policies = await self.config.get_password_policies()
        self.assertIsInstance(password_policies, PasswordPoliciesConfig)
    
    async def test_get_product_packages(self):
        product_packages = await self.config.get_product_packages()
        self.assertIsInstance(product_packages, ProductPackageResponseList)
    
    async def test_get_current_product_package(self):
        product_package = await self.config.get_current_product_package()
        self.assertIsInstance(product_package, ProductPackageResponseList)
    
    async def test_get_s3_tags(self):
        logging.disable(level=logging.CRITICAL)
        try:
            s3_tags = await self.config.get_s3_tags()
            self.assertIsInstance(s3_tags, S3TagList)
        except HTTPPreconditionsFailedError:
            self.skipTest("S3 tags not configured")
        finally:
            logging.disable(level=logging.DEBUG)
    

if __name__ == "__main__":
    unittest.main()