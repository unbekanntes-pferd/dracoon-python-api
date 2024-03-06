import unittest
import respx

import json
from datetime import datetime

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.users import DRACOONUsers

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
DEFAULT_STRING = 'string'
DEFAULT_DATE = '2020-01-01T00:00:00.000Z'
DEFAULT_PARSED_DATE = datetime.strptime(DEFAULT_DATE, '%Y-%m-%dT%H:%M:%S.%fZ')


class TestAsyncDRACOONUsers(unittest.IsolatedAsyncioTestCase): 
    def setUp(self) -> None:
        return super().setUp()
       
    @respx.mock
    async def asyncSetUp(self) -> None:
        self.client = DRACOONClient(base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, raise_on_err=True)
        with open('tests/responses/auth/auth_ok.json', 'r') as json_file:
     
            login_json = json.load(json_file)
            login_mock = respx.post(f'{BASE_URL}/oauth/token').respond(200, json=login_json)
            await self.client.connect(username='test_user', password='test_password', connection_type=OAuth2ConnectionType.password_flow)

            assert login_mock.called
            assert self.client.connected

            self.users = DRACOONUsers(self.client)

            return await super().asyncSetUp()
       
    @respx.mock
    async def test_get_users(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users').respond(200, json=get_users_json)
            users = await self.users.get_users()
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False

    
    @respx.mock
    async def test_get_users_with_filter(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            filter = 'type:eq:file'
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset=0&filter={filter}').respond(200, json=get_users_json)
            users = await self.users.get_users(filter=filter)
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False

    @respx.mock
    async def test_get_users_with_sort(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            sort = 'name:asc'
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset=0&sort={sort}').respond(200, json=get_users_json)
            users = await self.users.get_users(sort=sort)
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False             

    @respx.mock
    async def test_get_users_with_limit(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            limit = 1
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset=0&limit={limit}').respond(200, json=get_users_json)
            users = await self.users.get_users(limit=limit)
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False

    @respx.mock
    async def test_get_users_with_offset(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            offset = 100
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset={offset}').respond(200, json=get_users_json)
            users = await self.users.get_users(offset=offset)
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False

    @respx.mock
    async def test_get_users_with_roles(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset=0&include_roles=true').respond(200, json=get_users_json)
            users = await self.users.get_users(include_roles=True)
            assert get_users_mock.called
            assert len(users.items) == 1
            assert users.items[0].id == 1
            assert users.items[0].userName == DEFAULT_STRING
            assert users.items[0].firstName == DEFAULT_STRING
            assert users.items[0].lastName == DEFAULT_STRING
            assert users.items[0].email == DEFAULT_STRING
            #assert users.items[0].createdAt == DEFAULT_PARSED_DATE
            #assert users.items[0].lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert users.items[0].isEncryptionEnabled == True
            assert users.items[0].isLocked == False

    @respx.mock
    async def test_get_users_with_attributes(self):
        with open('tests/responses/users/users_ok.json', 'r') as json_file:
            get_users_json = json.load(json_file)
            get_users_mock = respx.get(f'{BASE_URL}/api/v4/users?offset=0&include_attributes=true').respond(200, json=get_users_json)
            users = await self.users.get_users(include_attributes=True)
            assert get_users_mock.called
            assert len(users.items) == 1
            user = users.items[0]
            assert user.id == 1
            assert user.userName == DEFAULT_STRING
            assert user.firstName == DEFAULT_STRING
            assert user.lastName == DEFAULT_STRING
            assert user.email == DEFAULT_STRING
            #assert user.createdAt == DEFAULT_PARSED_DATE
            #assert user.lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert user.isEncryptionEnabled == True
            assert user.isLocked == False

    @respx.mock
    async def test_create_user(self):
        with open('tests/responses/users/user_ok.json', 'r') as json_file:
            create_user_json = json.load(json_file)
            create_user_mock = respx.post(f'{BASE_URL}/api/v4/users').respond(201, json=create_user_json)
            user_payload = self.users.make_local_user(first_name='test', last_name='test', email='test@dracoon.com', login='local.user')
            user = await self.users.create_user(user=user_payload)
            assert create_user_mock.called
            assert user.id == 1
            assert user.userName == DEFAULT_STRING
            assert user.firstName == DEFAULT_STRING
            assert user.lastName == DEFAULT_STRING
            assert user.email == DEFAULT_STRING
            #assert user.createdAt == DEFAULT_PARSED_DATE
            #assert user.lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert user.isEncryptionEnabled == True
            assert user.isLocked == False

    @respx.mock
    async def test_get_user(self):
        with open('tests/responses/users/user_ok.json', 'r') as json_file:
            create_user_json = json.load(json_file)
            user_id = 1
            create_user_mock = respx.get(f'{BASE_URL}/api/v4/users/{user_id}').respond(201, json=create_user_json)
            user = await self.users.get_user(user_id=user_id)
            assert create_user_mock.called
            assert user.id == 1
            assert user.userName == DEFAULT_STRING
            assert user.firstName == DEFAULT_STRING
            assert user.lastName == DEFAULT_STRING
            assert user.email == DEFAULT_STRING
            #assert user.createdAt == DEFAULT_PARSED_DATE
            #assert user.lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert user.isEncryptionEnabled == True
            assert user.isLocked == False

    @respx.mock
    async def test_update_user(self):
        with open('tests/responses/users/user_ok.json', 'r') as json_file:
            create_user_json = json.load(json_file)
            user_id = 1
            update = self.users.make_user_update(first_name='test')
            create_user_mock = respx.put(f'{BASE_URL}/api/v4/users/{user_id}').respond(201, json=create_user_json)
            user = await self.users.update_user(user_id=user_id, user_update=update)
            assert create_user_mock.called
            assert user.id == 1
            assert user.userName == DEFAULT_STRING
            assert user.firstName == DEFAULT_STRING
            assert user.lastName == DEFAULT_STRING
            assert user.email == DEFAULT_STRING
            #assert user.createdAt == DEFAULT_PARSED_DATE
            #assert user.lastLoginSuccessAt == DEFAULT_PARSED_DATE
            assert user.isEncryptionEnabled == True
            assert user.isLocked == False
        
    @respx.mock
    async def test_delete_user(self):
        user_id = 1
        delete_user_mock = respx.delete(f'{BASE_URL}/api/v4/users/{user_id}').respond(204)
        await self.users.delete_user(user_id=user_id)
        assert delete_user_mock.called
    




              
              
