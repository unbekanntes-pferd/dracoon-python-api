import asyncio
import unittest
import dotenv
import os

from dracoon import DRACOONClient, OAuth2ConnectionType
from dracoon.errors import DRACOONHttpError
from dracoon.user import DRACOONUser
from dracoon.user.models import UpdateAccount, UserAccount
from dracoon.crypto.models import UserKeyPairContainer, UserKeyPairVersion


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOONUser(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.user = DRACOONUser(dracoon_client=self.dracoon)
        assert isinstance(self.user, DRACOONUser)
        
    
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_user_info(self):
        
        user_info = await self.user.get_account_information(more_info=True)
        assert isinstance(user_info, UserAccount)
        
    async def test_account_update(self):

        account_update = self.user.make_account_update(phone='999999999')
        assert isinstance(account_update, UpdateAccount)
        
        account_update_res = await self.user.update_account_information(account_update=account_update)
        assert account_update_res.phone == '999999999'
        
    
    async def test_set_get_2048_keypair(self):
    
        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        keypair_2048 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
        assert keypair_2048 == None
        
        keypair_2048 = await self.user.get_user_keypair(version=UserKeyPairVersion.RSA2048)

        assert isinstance(keypair_2048, UserKeyPairContainer)
        assert keypair_2048.privateKeyContainer.version == UserKeyPairVersion.RSA2048.value
        assert keypair_2048.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value
        
    
    async def test_delete_2048_keypair(self):

        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        keypair_2048 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
        assert keypair_2048 == None

        del_keypair = await self.user.delete_user_keypair(version=UserKeyPairVersion.RSA2048)
        assert del_keypair == None
        
    
    async def test_set_get_4096_keypair(self):
        
        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        
        keypair_4096 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096)
        assert keypair_4096 == None

        keypair_4096 = await self.user.get_user_keypair()

        assert isinstance(keypair_4096, UserKeyPairContainer)
        assert keypair_4096.privateKeyContainer.version == UserKeyPairVersion.RSA4096.value
        assert keypair_4096.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value
        
    
    async def test_delete_4096_keypair(self):

        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass

        secret = 'VerySecret123!'
        
        keypair_4096 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096)
        assert keypair_4096 == None
        
class TestAsyncDRACOONServerUser(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url_server, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.user = DRACOONUser(dracoon_client=self.dracoon)
        assert isinstance(self.user, DRACOONUser)
        
    
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_user_info(self):
        
        user_info = await self.user.get_account_information(more_info=True)
        assert isinstance(user_info, UserAccount)
        
    async def test_account_update(self):

        account_update = self.user.make_account_update(phone='999999999')
        assert isinstance(account_update, UpdateAccount)
        
        account_update_res = await self.user.update_account_information(account_update=account_update)
        assert account_update_res.phone == '999999999'
        
    
    async def test_set_get_2048_keypair(self):
    
        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        keypair_2048 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
        assert keypair_2048 == None
        
        keypair_2048 = await self.user.get_user_keypair(version=UserKeyPairVersion.RSA2048)

        assert isinstance(keypair_2048, UserKeyPairContainer)
        assert keypair_2048.privateKeyContainer.version == UserKeyPairVersion.RSA2048.value
        assert keypair_2048.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value
        
    
    async def test_delete_2048_keypair(self):

        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        keypair_2048 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
        assert keypair_2048 == None

        del_keypair = await self.user.delete_user_keypair(version=UserKeyPairVersion.RSA2048)
        assert del_keypair == None
        
    
    async def test_set_get_4096_keypair(self):
        
        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass
        
        secret = 'VerySecret123!'
        
        keypair_4096 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096)
        assert keypair_4096 == None

        keypair_4096 = await self.user.get_user_keypair()

        assert isinstance(keypair_4096, UserKeyPairContainer)
        assert keypair_4096.privateKeyContainer.version == UserKeyPairVersion.RSA4096.value
        assert keypair_4096.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value
        
    
    async def test_delete_4096_keypair(self):

        try:
            await self.user.delete_user_keypair()
        except DRACOONHttpError:
            pass

        secret = 'VerySecret123!'
        
        keypair_4096 = await self.user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096)
        assert keypair_4096 == None
        

if __name__ == '__main__':
    unittest.main()

    

   


