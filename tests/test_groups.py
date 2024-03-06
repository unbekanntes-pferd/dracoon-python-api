import unittest
import respx

import json
from datetime import datetime

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.groups import DRACOONGroups
from dracoon.groups.responses import UserType

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
DEFAULT_STRING = 'string'
DEFAULT_DATE = '2020-01-01T00:00:00.000Z'
DEFAULT_PARSED_DATE = datetime.strptime(DEFAULT_DATE, '%Y-%m-%dT%H:%M:%S.%fZ')


class TestAsyncDRACOONGroups(unittest.IsolatedAsyncioTestCase):
    def setUp(self) -> None:
        with open('tests/responses/groups/groups_ok.json', 'r') as json_file:
            self.groups_json = json.load(json_file)

        with open('tests/responses/groups/group_ok.json', 'r') as json_file:
            self.group_json = json.load(json_file)

        return super().setUp()

    def assert_group(self, group) -> None:
        assert group.id == 1
        assert group.name == DEFAULT_STRING
        # assert group.createdAt == DEFAULT_PARSED_DATE
        # assert group.updatedAt == DEFAULT_PARSED_DATE
        created_by = group.createdBy
        updated_by = group.updatedBy
        assert created_by.id == 2
        assert created_by.userName == DEFAULT_STRING
        assert created_by.firstName == DEFAULT_STRING
        assert created_by.lastName == DEFAULT_STRING
        assert created_by.email == DEFAULT_STRING
        assert created_by.avatarUuid == DEFAULT_STRING
        assert created_by.userType == UserType.internal
        assert updated_by.id == 2
        assert updated_by.userName == DEFAULT_STRING
        assert updated_by.firstName == DEFAULT_STRING
        assert updated_by.lastName == DEFAULT_STRING
        assert updated_by.email == DEFAULT_STRING
        assert updated_by.avatarUuid == DEFAULT_STRING
        assert updated_by.userType == UserType.internal

    @respx.mock
    async def asyncSetUp(self) -> None:
        self.client = DRACOONClient(
            base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, raise_on_err=True)
        with open('tests/responses/auth/auth_ok.json', 'r') as json_file:

            login_json = json.load(json_file)
            login_mock = respx.post(
                f'{BASE_URL}/oauth/token').respond(200, json=login_json)
            await self.client.connect(username='test_user', password='test_password', connection_type=OAuth2ConnectionType.password_flow)

            assert login_mock.called
            assert self.client.connected

            self.groups = DRACOONGroups(self.client)

            return await super().asyncSetUp()

    @respx.mock
    async def test_get_groups(self):
        groups_mock = respx.get(
            f'{BASE_URL}/api/v4/groups').respond(200, json=self.groups_json)
        groups = await self.groups.get_groups()
        assert groups_mock.called
        assert len(groups.items) == 1
        group = groups.items[0]
        self.assert_group(group)

    @respx.mock
    async def test_get_groups_with_filter(self):
        filter = 'name:cn:test'
        groups_mock = respx.get(
            f'{BASE_URL}/api/v4/groups?offset=0&filter={filter}').respond(200, json=self.groups_json)
        groups = await self.groups.get_groups(filter=filter)
        assert groups_mock.called
        assert len(groups.items) == 1
        group = groups.items[0]
        self.assert_group(group)

    @respx.mock
    async def test_get_groups_with_sort(self):
        sort = 'name:asc'
        groups_mock = respx.get(
            f'{BASE_URL}/api/v4/groups?offset=0&sort={sort}').respond(200, json=self.groups_json)
        groups = await self.groups.get_groups(sort=sort)
        assert groups_mock.called
        assert len(groups.items) == 1
        group = groups.items[0]
        self.assert_group(group)

    @respx.mock
    async def test_get_groups_with_offset(self):
        offset = 100
        groups_mock = respx.get(
            f'{BASE_URL}/api/v4/groups?offset={offset}').respond(200, json=self.groups_json)
        groups = await self.groups.get_groups(offset=offset)
        assert groups_mock.called
        assert len(groups.items) == 1
        group = groups.items[0]
        self.assert_group(group)

    @respx.mock
    async def test_get_groups_with_limit(self):
        limit = 100
        groups_mock = respx.get(
            f'{BASE_URL}/api/v4/groups?offset=0&limit={limit}').respond(200, json=self.groups_json)
        groups = await self.groups.get_groups(limit=limit)
        assert groups_mock.called
        assert len(groups.items) == 1
        group = groups.items[0]
        self.assert_group(group)

    @respx.mock
    async def test_create_group(self):
        group_mock = respx.post(
            f'{BASE_URL}/api/v4/groups').respond(200, json=self.group_json)
        group_payload = self.groups.make_group(name=DEFAULT_STRING)
        group = await self.groups.create_group(group_payload)
        assert group_mock.called
        self.assert_group(group)

    @respx.mock
    async def test_get_group(self):
        group_id = 1
        group_mock = respx.get(
            f'{BASE_URL}/api/v4/groups/{group_id}').respond(200, json=self.group_json)
        group = await self.groups.get_group(group_id)
        assert group_mock.called
        self.assert_group(group)

    @respx.mock
    async def test_update_group(self):
        group_id = 1
        group_payload = self.groups.make_group_update(name=DEFAULT_STRING)
        group_mock = respx.put(
            f'{BASE_URL}/api/v4/groups/{group_id}').respond(200, json=self.group_json)
        group = await self.groups.update_group(group_id, group_payload)
        assert group_mock.called
        self.assert_group(group)

    @respx.mock
    async def test_delete_group(self):
        group_id = 1
        group_mock = respx.delete(
            f'{BASE_URL}/api/v4/groups/{group_id}').respond(204)
        group = await self.groups.delete_group(group_id)
        assert group_mock.called
