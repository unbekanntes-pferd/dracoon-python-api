import os
import asyncio
import unittest
import dotenv
from dracoon import DRACOONClient, OAuth2ConnectionType
from dracoon.public import DRACOONPublic
from dracoon.public.responses import AuthADInfoList, AuthOIDCInfoList, SystemInfo

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOONPublic(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)

        self.public = DRACOONPublic(dracoon_client=self.dracoon)
        self.assertIsInstance(self.public, DRACOONPublic)

    async def asyncTearDown(self) -> None:
        await self.dracoon.disconnect()
        
    async def test_get_system_info(self):
        system_info = await self.public.get_system_info()
        self.assertIsInstance(system_info, SystemInfo)
 
    async def test_get_ad_info(self):
        auth_ad_info = await self.public.get_auth_ad_info()
        self.assertIsInstance(auth_ad_info, AuthADInfoList)


    async def test_get_oidc_info(self):
        auth_oidc_info = await self.public.get_auth_openid_info()
        self.assertIsInstance(auth_oidc_info, AuthOIDCInfoList)
        
class TestAsyncDRACOONServerPublic(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url_server, client_id=client_id, client_secret=client_secret, raise_on_err=True)

        self.public = DRACOONPublic(dracoon_client=self.dracoon)
        self.assertIsInstance(self.public, DRACOONPublic)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.disconnect()
        
    async def test_get_system_info(self):
        system_info = await self.public.get_system_info()
        self.assertIsInstance(system_info, SystemInfo)
 

    async def test_get_ad_info(self):
        auth_ad_info = await self.public.get_auth_ad_info()
        self.assertIsInstance(auth_ad_info, AuthADInfoList)


    async def test_get_oidc_info(self):
        auth_oidc_info = await self.public.get_auth_openid_info()
        self.assertIsInstance(auth_oidc_info, AuthOIDCInfoList)
    

if __name__ == '__main__':
    unittest.main()


    

   


