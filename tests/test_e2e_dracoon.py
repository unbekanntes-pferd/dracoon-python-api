import os
import asyncio
import unittest
import dotenv

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon import DRACOON
from dracoon.errors import DRACOONCryptoError

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOON(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
 
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_wrong_enryption_password(self):
        new_kp = await self.dracoon.user.set_user_keypair(secret='Test1234!')
        with self.assertRaises(DRACOONCryptoError):
            kp = await self.dracoon.get_keypair(secret="Wrong")
        await self.dracoon.user.delete_user_keypair()
        
 
if __name__ == "__main__":
    unittest.main()