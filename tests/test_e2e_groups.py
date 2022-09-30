import os
import asyncio
import unittest
import dotenv
from dracoon import DRACOONClient, OAuth2ConnectionType
from dracoon.groups import DRACOONGroups
from dracoon.groups.models import CreateGroup, UpdateGroup
from dracoon.groups.responses import Group, GroupList, GroupUserList, LastAdminGroupRoomList, UserType
from dracoon.user import DRACOONUser
from dracoon.user.responses import RoleList

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')

class TestAsyncDRACOONGroups(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.groups = DRACOONGroups(dracoon_client=self.dracoon)
        assert isinstance(self.groups, DRACOONGroups)
        
        self.user = DRACOONUser(dracoon_client=self.dracoon)
  
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
        
    async def test_get_groups(self):
        group_list = await self.groups.get_groups()
        assert isinstance(group_list, GroupList)
        
        
    async def test_create_group(self):
        new_group = self.groups.make_group(name='CREATE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)

        await self.groups.delete_group(group_id=group.id)

    async def test_update_group(self):
        new_group = self.groups.make_group(name='UPDATE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        update_name = 'THIS IS ANOTHER TEST'
        
        update = self.groups.make_group_update(name=update_name)
        
        assert isinstance(update, UpdateGroup)

        updated_group = await self.groups.update_group(group_id=group.id, group_update=update)
        assert updated_group.name == update_name
        
        await self.groups.delete_group(group_id=group.id)

    async def test_get_group_roles(self):

        new_group = self.groups.make_group(name='GROUP ROLES TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        group_roles = await self.groups.get_group_roles(group_id=group.id)
        assert isinstance(group_roles, RoleList)
        
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_add_group_users(self):

        new_group = self.groups.make_group(name='GROUP USERS TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        user_info = await self.user.get_account_information()
        
        await self.groups.add_group_users(group_id=group.id, user_list=[user_info.id])
        
        group_users = await self.groups.get_group_users(group_id=group.id)
        assert isinstance(group_users, GroupUserList)
        assert len(group_users.items) == 1
        group_user = group_users.items[0]
        assert group_user.isMember == True
        assert group_user.userInfo.lastName == user_info.lastName
        assert group_user.userInfo.firstName == user_info.firstName
        assert group_user.userInfo.email == user_info.email
        assert group_user.userInfo.id == user_info.id
        assert group_user.userInfo.userName == user_info.userName
        assert group_user.userInfo.userType == UserType.internal
                
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_group_last_admins(self):

        new_group = self.groups.make_group(name='GROUP LAST ADMIN TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        group_last_admin_rooms = await self.groups.get_group_last_admin_rooms(group_id=group.id)
        assert isinstance(group_last_admin_rooms, LastAdminGroupRoomList)
        
        await self.groups.delete_group(group_id=group.id)
        
    async def test_delete_group_users(self):

        new_group = self.groups.make_group(name='GROUP USERS DELETE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        user_info = await self.user.get_account_information()
        
        await self.groups.add_group_users(group_id=group.id, user_list=[user_info.id])
        
        group_users = await self.groups.get_group_users(group_id=group.id)
        assert len(group_users.items) == 1
        
        await self.groups.delete_group_users(group_id=group.id, user_list=[user_info.id])

        group_users = await self.groups.get_group_users(group_id=group.id)
        assert len(group_users.items) == 0

        await self.groups.delete_group(group_id=group.id)
    
    async def test_delete_group(self):
        
        new_group = self.groups.make_group(name='DELETE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        del_group = await self.groups.delete_group(group_id=group.id)
        assert del_group == None

class TestAsyncDRACOONServerGroups(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url_server, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.groups = DRACOONGroups(dracoon_client=self.dracoon)
        assert isinstance(self.groups, DRACOONGroups)
        
        self.user = DRACOONUser(dracoon_client=self.dracoon)
  
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
        
    async def test_get_groups(self):
        group_list = await self.groups.get_groups()
        assert isinstance(group_list, GroupList)
        
        
    async def test_create_group(self):
        new_group = self.groups.make_group(name='CREATE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)

        await self.groups.delete_group(group_id=group.id)

    async def test_update_group(self):
        new_group = self.groups.make_group(name='UPDATE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        update_name = 'THIS IS ANOTHER TEST'
        
        update = self.groups.make_group_update(name=update_name)
        
        assert isinstance(update, UpdateGroup)

        updated_group = await self.groups.update_group(group_id=group.id, group_update=update)
        assert updated_group.name == update_name
        
        await self.groups.delete_group(group_id=group.id)

    async def test_get_group_roles(self):

        new_group = self.groups.make_group(name='GROUP ROLES TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        group_roles = await self.groups.get_group_roles(group_id=group.id)
        assert isinstance(group_roles, RoleList)
        
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_add_group_users(self):

        new_group = self.groups.make_group(name='GROUP USERS TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        user_info = await self.user.get_account_information()
        
        await self.groups.add_group_users(group_id=group.id, user_list=[user_info.id])
        
        group_users = await self.groups.get_group_users(group_id=group.id)
        assert isinstance(group_users, GroupUserList)
        assert len(group_users.items) == 1
        group_user = group_users.items[0]
        assert group_user.isMember == True
        assert group_user.userInfo.lastName == user_info.lastName
        assert group_user.userInfo.firstName == user_info.firstName
        assert group_user.userInfo.email == user_info.email
        assert group_user.userInfo.id == user_info.id
        assert group_user.userInfo.userName == user_info.userName
        assert group_user.userInfo.userType == UserType.internal
                
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_group_last_admins(self):

        new_group = self.groups.make_group(name='GROUP LAST ADMIN TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        group_last_admin_rooms = await self.groups.get_group_last_admin_rooms(group_id=group.id)
        assert isinstance(group_last_admin_rooms, LastAdminGroupRoomList)
        
        await self.groups.delete_group(group_id=group.id)
        
    async def test_delete_group_users(self):

        new_group = self.groups.make_group(name='GROUP USERS DELETE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        user_info = await self.user.get_account_information()
        
        await self.groups.add_group_users(group_id=group.id, user_list=[user_info.id])
        
        group_users = await self.groups.get_group_users(group_id=group.id)
        assert len(group_users.items) == 1
        
        await self.groups.delete_group_users(group_id=group.id, user_list=[user_info.id])

        group_users = await self.groups.get_group_users(group_id=group.id)
        assert len(group_users.items) == 0

        await self.groups.delete_group(group_id=group.id)
    
    async def test_delete_group(self):
        
        new_group = self.groups.make_group(name='DELETE TEST')
        assert isinstance(new_group, CreateGroup)
        group = await self.groups.create_group(new_group)
        assert isinstance(group, Group)
        
        del_group = await self.groups.delete_group(group_id=group.id)
        assert del_group == None
        

if __name__ == '__main__':
    unittest.main()