import unittest
import respx
import asyncio

import json
from datetime import datetime

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.user import DRACOONUser
from dracoon.crypto import create_plain_userkeypair, encrypt_private_key
from dracoon.crypto.models import UserKeyPairVersion

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
DEFAULT_STRING = 'string'
DEFAULT_DATE = '2020-01-01T00:00:00.000Z'
DEFAULT_PARSED_DATE = datetime.strptime(DEFAULT_DATE, '%Y-%m-%dT%H:%M:%S.%fZ')


class TestAsyncDRACOONUser(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:

        with open('tests/responses/user_info_ok.json', 'r') as json_file:
            self.user_info_json = json.load(json_file)
        
        with open('tests/responses/keypair_ok.json', 'r') as json_file:
            self.keypair_json = json.load(json_file)

        return super().setUp()

    def assert_user_info(self, user_info) -> None:
        assert user_info.id == 1
        assert user_info.userName == DEFAULT_STRING
        assert user_info.firstName == DEFAULT_STRING
        assert user_info.lastName == DEFAULT_STRING
        assert user_info.email == DEFAULT_STRING
        assert user_info.isEncryptionEnabled == True
        assert user_info.isLocked == False
        assert user_info.language == DEFAULT_STRING
        assert user_info.phone == DEFAULT_STRING
        assert user_info.mustSetEmail == False
        assert user_info.needsToAcceptEULA == False
        assert user_info.isEncryptionEnabled == True
        roles = user_info.userRoles.items
        nonmember_role = roles[0]
        user_role = roles[1]
        assert nonmember_role.id == 6
        assert nonmember_role.name == 'NONMEMBER_VIEWER'
        assert user_role.id == 7
        assert user_role.name == 'USER'
        assert user_info.authData.method == 'basic'
    

    @respx.mock
    async def asyncSetUp(self) -> None:

        # needed because keypair generation takes a second
        asyncio.get_running_loop().set_debug(False)

        self.client = DRACOONClient(
            base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, raise_on_err=True)
        with open('tests/responses/auth/auth_ok.json', 'r') as json_file:
            login_json = json.load(json_file)
            login_mock = respx.post(
                f'{BASE_URL}/oauth/token').respond(200, json=login_json)
            await self.client.connect(username='test_user', password='test_password', connection_type=OAuth2ConnectionType.password_flow)

            assert login_mock.called
            assert self.client.connected

            self.user = DRACOONUser(self.client)

            return await super().asyncSetUp()
    
    @respx.mock
    async def test_get_user_info(self):
        get_user_info_mock = respx.get(
            f'{BASE_URL}/api/v4/user/account').respond(200, json=self.user_info_json)
        user_info = await self.user.get_account_information()
        self.assert_user_info(user_info)
        assert get_user_info_mock.called

    @respx.mock
    async def test_get_user_info_with_more_info(self):
        get_user_info_mock = respx.get(
            f'{BASE_URL}/api/v4/user/account?more_info=true').respond(200, json=self.user_info_json)
        user_info = await self.user.get_account_information(more_info=True)
        self.assert_user_info(user_info)
        assert get_user_info_mock.called
    
    @respx.mock
    async def test_update_user_info(self):
        update = self.user.make_account_update(user_name='test_user')
        update_user_info_mock = respx.put(
            f'{BASE_URL}/api/v4/user/account').respond(200, json=self.user_info_json)
        user_info = await self.user.update_account_information(account_update=update)
        self.assert_user_info(user_info)
        assert update_user_info_mock.called

    @respx.mock
    async def test_get_user_keypair(self):
        get_keypair_mock = respx.get(
            f'{BASE_URL}/api/v4/user/account/keypair').respond(200, json=self.keypair_json)
        keypair = await self.user.get_user_keypair()
        assert keypair.privateKeyContainer.createdBy == 1
        assert keypair.publicKeyContainer.createdBy == 1
        assert keypair.privateKeyContainer.version == 'RSA-4096'
        assert get_keypair_mock.called
    
    @respx.mock
    async def test_set_user_keypair_4096(self):
        set_keypair_mock = respx.post(f'{BASE_URL}/api/v4/user/account/keypair').respond(204)
        await self.user.set_user_keypair(secret='test', version=UserKeyPairVersion.RSA4096)
        assert set_keypair_mock.called

    @respx.mock
    async def test_delete_user_keypair_4096(self):
        set_keypair_mock = respx.delete(f'{BASE_URL}/api/v4/user/account/keypair?version=RSA-4096').respond(204)
        await self.user.delete_user_keypair(version=UserKeyPairVersion.RSA4096)
        assert set_keypair_mock.called