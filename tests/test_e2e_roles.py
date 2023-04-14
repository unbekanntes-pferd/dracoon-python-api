
import os
import asyncio
import unittest
import dotenv
import logging

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.user.responses import RoleList
from dracoon.roles import DRACOONRoles
from dracoon.roles.responses import RoleGroupList, RoleUserList
from dracoon.roles.models import GroupIds, UserIds
from dracoon.users import DRACOONUsers
from dracoon.groups import DRACOONGroups

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOONRoles(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.roles = DRACOONRoles(dracoon_client=self.dracoon)
        self.users = DRACOONUsers(dracoon_client=self.dracoon)
        self.groups = DRACOONGroups(dracoon_client=self.dracoon)
        self.assertIsInstance(self.roles, DRACOONRoles)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_roles(self):
        roles = await self.roles.get_roles()
        self.assertIsInstance(roles, RoleList)

    async def test_get_groups_with_role(self):
        role_groups = await self.roles.get_groups_with_role(role_id=1)
        self.assertIsInstance(role_groups, RoleGroupList)

    async def test_assign_groups_to_role(self):
        test_group = self.groups.make_group(name="test-role-group")
        group = await self.groups.create_group(group=test_group)
        group_ids = [group.id]
        group_ids = self.roles.make_user_group_ids(ids=group_ids, is_user=False)
        self.assertIsInstance(group_ids, GroupIds)
        
        role_groups = await self.roles.assign_groups_to_role(role_id=1, groups=group_ids)
        self.assertIsInstance(role_groups, RoleGroupList)
        
        await self.groups.delete_group(group_id=group.id)

    async def test_remove_groups_from_role(self):
        test_group = self.groups.make_group(name="test-role-group-removal")
        group = await self.groups.create_group(group=test_group)
        group_ids = [group.id]
        group_ids = self.roles.make_user_group_ids(ids=group_ids, is_user=False)
        self.assertIsInstance(group_ids, GroupIds)
        
        role_groups = await self.roles.assign_groups_to_role(role_id=1, groups=group_ids)
        self.assertIsInstance(role_groups, RoleGroupList)
        
        del_groups = await self.roles.remove_groups_from_role(role_id=1, groups=group_ids)
        self.assertIsInstance(del_groups, RoleGroupList)
        
        await self.groups.delete_group(group_id=group.id)

    async def test_get_users_with_role(self):
        role_users = await self.roles.get_users_with_role(role_id=1)
        self.assertIsInstance(role_users, RoleUserList)

    async def test_assign_users_to_role(self):
        test_user = self.users.make_local_user(first_name="test-role", last_name="test-role", email="foo@dracoon.com", login="test-role-assign")
        user = await self.users.create_user(user=test_user)
        user_ids = [user.id]
        user_ids = self.roles.make_user_group_ids(ids=user_ids)
        self.assertIsInstance(user_ids, UserIds)
        
        role_users = await self.roles.assign_users_to_role(role_id=1, users=user_ids)
        self.assertIsInstance(role_users, RoleUserList)
        
        await self.users.delete_user(user_id=user.id)

    async def test_remove_users_from_role(self):
        test_user = self.users.make_local_user(first_name="test-role-removal", last_name="test-role-removal", email="foo@dracoon.com", login="test-role-removal")
        user = await self.users.create_user(user=test_user)
        user_ids = [user.id]
        user_ids = self.roles.make_user_group_ids(ids=user_ids)
        self.assertIsInstance(user_ids, UserIds)
        
        role_users = await self.roles.assign_users_to_role(role_id=1, users=user_ids)
        self.assertIsInstance(role_users, RoleUserList)
         
        del_users = await self.roles.remove_users_from_role(role_id=1, users=user_ids)
        self.assertIsInstance(del_users, RoleUserList)
        
        await self.users.delete_user(user_id=user.id)
    
if __name__ == "__main__":
    unittest.main()