import os
import asyncio
import unittest
import dotenv
from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.groups import DRACOONGroups
from dracoon.nodes import DRACOONNodes
from dracoon.public import DRACOONPublic
from dracoon.user import DRACOONUser
from dracoon.users import DRACOONUsers
from dracoon.user.responses import AttributesResponse, LastAdminUserRoomList, UserData, UserGroupList, UserList, RoleList
from dracoon.users.models import AttributeEntry, CreateUser, UpdateUser, UpdateUserAttributes, UserAuthData


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')

class TestAsyncDRACOONUsers(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.users = DRACOONUsers(dracoon_client=self.dracoon)
        self.assertIsInstance(self.users, DRACOONUsers)
        
        self.public = DRACOONPublic(dracoon_client=self.dracoon)
        self.groups = DRACOONGroups(dracoon_client=self.dracoon)
        self.user = DRACOONUser(dracoon_client=self.dracoon)
        self.nodes = DRACOONNodes(dracoon_client=self.dracoon)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_users(self):
        user_list = await self.users.get_users()
        self.assertIsInstance(user_list, UserList)
        
    async def test_get_user(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.user') 
        user = await self.users.create_user(local_user)
        
        new_user = await self.users.get_user(user_id=user.id)
        
        self.assertEqual(new_user.id, user.id)
        self.assertEqual(new_user.firstName, local_user.firstName)
        self.assertEqual(new_user.lastName, local_user.lastName)
        self.assertEqual(new_user.email, local_user.email)
        self.assertEqual(new_user.userName, local_user.userName)
        self.assertIsInstance(new_user, UserData)
        
        await self.users.delete_user(user_id=user.id)
        
    async def test_create_local_user(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.user')
        self.assertIsInstance(local_user, CreateUser)
        
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'basic')
        await self.users.delete_user(user_id=user.id)
        
    async def test_create_oidc_user(self):
        oidc_info = await self.public.get_auth_openid_info()
        if len(oidc_info.items) > 0:
            oidc_id = oidc_info.items[0].id
        else:
            self.skipTest("No OIDC config present")
        oidc_user = self.users.make_oidc_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='oidc.login', oidc_id=oidc_id)
        self.assertIsInstance(oidc_user, CreateUser)

        user = await self.users.create_user(oidc_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'openid')
        await self.users.delete_user(user_id=user.id)
    
    async def test_create_ad_user(self):
        ad_info = await self.public.get_auth_ad_info()
        if len(ad_info.items) > 0:
            ad_id = ad_info.items[0].id
        else:
            self.skipTest("No AD config present")
        ad_user = self.users.make_ad_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='ad.login', ad_id=ad_id)
        self.assertIsInstance(ad_user, CreateUser)

        user = await self.users.create_user(ad_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'active_directory')
        await self.users.delete_user(user_id=user.id)
        
    async def test_update_user(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.update.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'basic')
        
        login = 'oidc.update.test'
        oidc_info = await self.public.get_auth_openid_info()
        oidc_id = oidc_info.items[0].id
        
        auth = self.users.make_auth_data(method='openid', login=login, oidc_id=oidc_id)
        self.assertIsInstance(auth, UserAuthData)
        
        update = self.users.make_user_update(auth_data=auth)
        self.assertIsInstance(update, UpdateUser)
        
        updated_user = await self.users.update_user(user_id=user.id, user_update=update)
        self.assertEqual(updated_user.authData.login, login)
        self.assertEqual(updated_user.authData.method, 'openid')
        self.assertEqual(updated_user.id, user.id)

        await self.users.delete_user(user_id=user.id)
        
    async def test_create_user_mfa_enforced(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.update.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'basic')
        
        update = self.users.make_user_update(mfa_enforced=True)
        
        user_update = await self.users.update_user(user_id=user.id, user_update=update)
        
        self.assertTrue(user_update.isMfaEnforced)
        self.assertFalse(user_update.isMfaEnabled)
        
        await self.users.delete_user(user_id=user.id)
        
    async def test_delete_user(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.delete.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        user_delete = await self.users.delete_user(user_id=user.id)
        self.assertIsNone(user_delete)
    
    async def test_get_user_groups(self):
        new_group = self.groups.make_group(name='USER GROUPS TEST')
        group = await self.groups.create_group(group=new_group)
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.group.user') 
        user = await self.users.create_user(local_user)
  
        await self.groups.add_group_users(group_id=group.id, user_list=[user.id])
        
        user_groups = await self.users.get_user_groups(user_id=user.id)
        
        self.assertEqual(len(user_groups.items), 1)
        self.assertEqual(user_groups.items[0].name, group.name)
        self.assertEqual(user_groups.items[0].id, group.id)
        
        await self.users.delete_user(user_id=user.id)
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_user_roles(self):
        user_info = await self.user.get_account_information()
        user_roles = await self.users.get_user_roles(user_id=user_info.id)
        self.assertIsInstance(user_roles, RoleList)
        self.assertGreater(len(user_roles.items), 0)
    
    async def test_get_user_last_admin_rooms(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.lastadmin.user') 
        user = await self.users.create_user(local_user)
        
        new_room = self.nodes.make_room(name='TEST_LAST_ADMIN', admin_ids=[user.id])
        room = await self.nodes.create_room(room=new_room)
        
        user_last_admin_rooms = await self.users.get_user_last_admin_rooms(user_id=user.id)
        self.assertIsInstance(user_last_admin_rooms, LastAdminUserRoomList)
        self.assertEqual(len(user_last_admin_rooms.items), 1)
        self.assertEqual(user_last_admin_rooms.items[0].name, room.name)
        self.assertEqual(user_last_admin_rooms.items[0].id, room.id)
        
        await self.nodes.delete_node(node_id=room.id)
        await self.users.delete_user(user_id=user.id)
    
    async def test_user_attributes(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.attrib.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        
        user_attribute_payload = self.users.make_custom_user_attribute(key='test', value='test')
        attribute_list = [user_attribute_payload]

        self.assertIsInstance(user_attribute_payload, AttributeEntry)

        attributes_update = self.users.make_attributes_update(list=attribute_list)

        self.assertIsInstance(attributes_update, UpdateUserAttributes)

        attributes_update_res = await self.users.update_user_attributes(user_id=user.id, attributes=attributes_update)
        self.assertIsInstance(attributes_update_res, UserData)
        
        user_attributes = await self.users.get_user_attributes(user_id=user.id)
        self.assertIsInstance(user_attributes, AttributesResponse)
        self.assertEqual(user_attributes.items[0].key, 'test')
        self.assertEqual(user_attributes.items[0].value, 'test')
        
        attr_del = await self.users.delete_user_attribute(user_id=user.id, key='test')
        self.assertIsNone(attr_del)
        
        await self.users.delete_user(user_id=user.id)
        
class TestAsyncDRACOONServerUsers(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url_server, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.users = DRACOONUsers(dracoon_client=self.dracoon)
        self.assertIsInstance(self.users, DRACOONUsers)
        
        self.public = DRACOONPublic(dracoon_client=self.dracoon)
        self.groups = DRACOONGroups(dracoon_client=self.dracoon)
        self.user = DRACOONUser(dracoon_client=self.dracoon)
        self.nodes = DRACOONNodes(dracoon_client=self.dracoon)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_users(self):
        user_list = await self.users.get_users()
        self.assertIsInstance(user_list, UserList)

    async def test_get_user(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.user') 
        user = await self.users.create_user(local_user)
        
        new_user = await self.users.get_user(user_id=user.id)
        
        self.assertEqual(new_user.id, user.id)
        self.assertEqual(new_user.firstName, local_user.firstName)
        self.assertEqual(new_user.lastName, local_user.lastName)
        self.assertEqual(new_user.email, local_user.email)
        self.assertEqual(new_user.userName, local_user.userName)
        self.assertIsInstance(new_user, UserData)
        
        await self.users.delete_user(user_id=user.id)
    
    async def test_create_local_user(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.user')
        self.assertIsInstance(local_user, CreateUser)
        
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'basic')
        await self.users.delete_user(user_id=user.id)
        
    async def test_create_oidc_user(self):
        oidc_info = await self.public.get_auth_openid_info()
        if len(oidc_info.items) > 0:
            oidc_id = oidc_info.items[0].id
        else:
            self.skipTest("No OIDC config present")
        oidc_user = self.users.make_oidc_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='oidc.login', oidc_id=oidc_id)
        self.assertIsInstance(oidc_user, CreateUser)

        user = await self.users.create_user(oidc_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'openid')
        await self.users.delete_user(user_id=user.id)
    
    async def test_create_ad_user(self):
        ad_info = await self.public.get_auth_ad_info()
        if len(ad_info.items) > 0:
            ad_id = ad_info.items[0].id
        else:
            self.skipTest("No AD config present")
        ad_user = self.users.make_ad_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='ad.login', ad_id=ad_id)
        self.assertIsInstance(ad_user, CreateUser)

        user = await self.users.create_user(ad_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'active_directory')
        await self.users.delete_user(user_id=user.id)
        
    async def test_update_user(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.update.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        self.assertEqual(user.authData.method, 'basic')
        
        login = 'oidc.update.test'
        oidc_info = await self.public.get_auth_openid_info()
        oidc_id = oidc_info.items[0].id
        
        auth = self.users.make_auth_data(method='openid', login=login, oidc_id=oidc_id)
        self.assertIsInstance(auth, UserAuthData)
        
        update = self.users.make_user_update(auth_data=auth)
        self.assertIsInstance(update, UpdateUser)
        
        updated_user = await self.users.update_user(user_id=user.id, user_update=update)
        self.assertEqual(updated_user.authData.login, login)
        self.assertEqual(updated_user.authData.method, 'openid')
        self.assertEqual(updated_user.id, user.id)

        await self.users.delete_user(user_id=user.id)
        
    async def test_delete_user(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.delete.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        user_delete = await self.users.delete_user(user_id=user.id)
        self.assertIsNone(user_delete)
    
    async def test_get_user_groups(self):
        new_group = self.groups.make_group(name='USER GROUPS TEST')
        group = await self.groups.create_group(group=new_group)
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.group.user') 
        user = await self.users.create_user(local_user)
  
        await self.groups.add_group_users(group_id=group.id, user_list=[user.id])
        
        user_groups = await self.users.get_user_groups(user_id=user.id)
        
        self.assertEqual(len(user_groups.items), 1)
        self.assertEqual(user_groups.items[0].name, group.name)
        self.assertEqual(user_groups.items[0].id, group.id)
        
        await self.users.delete_user(user_id=user.id)
        await self.groups.delete_group(group_id=group.id)
    
    async def test_get_user_roles(self):
        user_info = await self.user.get_account_information()
        user_roles = await self.users.get_user_roles(user_id=user_info.id)
        self.assertIsInstance(user_roles, RoleList)
        self.assertGreater(len(user_roles.items), 0)
    
    async def test_get_user_last_admin_rooms(self):
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.lastadmin.user') 
        user = await self.users.create_user(local_user)
        
        new_room = self.nodes.make_room(name='TEST_LAST_ADMIN', admin_ids=[user.id])
        room = await self.nodes.create_room(room=new_room)
        
        user_last_admin_rooms = await self.users.get_user_last_admin_rooms(user_id=user.id)
        self.assertIsInstance(user_last_admin_rooms, LastAdminUserRoomList)
        self.assertEqual(len(user_last_admin_rooms.items), 1)
        self.assertEqual(user_last_admin_rooms.items[0].name, room.name)
        self.assertEqual(user_last_admin_rooms.items[0].id, room.id)
        
        await self.nodes.delete_node(node_id=room.id)
        await self.users.delete_user(user_id=user.id)
    
    async def test_user_attributes(self):
        
        local_user = self.users.make_local_user(first_name='test', last_name='test', email='test@unbekanntespferd.com', login='local.attrib.user') 
        user = await self.users.create_user(local_user)
        self.assertIsInstance(user, UserData)
        
        user_attribute_payload = self.users.make_custom_user_attribute(key='test', value='test')
        attribute_list = [user_attribute_payload]

        self.assertIsInstance(user_attribute_payload, AttributeEntry)

        attributes_update = self.users.make_attributes_update(list=attribute_list)

        self.assertIsInstance(attributes_update, UpdateUserAttributes)

        attributes_update_res = await self.users.update_user_attributes(user_id=user.id, attributes=attributes_update)
        self.assertIsInstance(attributes_update_res, UserData)
        
        user_attributes = await self.users.get_user_attributes(user_id=user.id)
        self.assertIsInstance(user_attributes, AttributesResponse)
        self.assertEqual(user_attributes.items[0].key, 'test')
        self.assertEqual(user_attributes.items[0].value, 'test')
        
        attr_del = await self.users.delete_user_attribute(user_id=user.id, key='test')
        self.assertEqual(attr_del, None)
        
        await self.users.delete_user(user_id=user.id)

if __name__ == '__main__':
    unittest.main()
