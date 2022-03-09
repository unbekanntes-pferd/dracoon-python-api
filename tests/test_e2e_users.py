from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.user.responses import AttributesResponse, LastAdminUserRoomList, UserData, UserGroupList, UserList, RoleList
from dracoon.users import DRACOONUsers
import dotenv
import os
import asyncio
from dracoon.users.models import AttributeEntry, CreateUser, UpdateUser, UpdateUserAttributes, UserAuthData


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

async def test_users_e2e():

    dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    users = DRACOONUsers(dracoon_client=dracoon)
    assert isinstance(users, DRACOONUsers)
    print('Connection test complete (/)')

    local_user = users.make_local_user(first_name='test', last_name='test', email='email@email.com')
    assert isinstance(local_user, CreateUser)
    print('Local user payload creation test passed (/)')

    ad_user = users.make_ad_user(first_name='test', last_name='test', email='email@email.com', login='ad.login', ad_id=4)
    assert isinstance(ad_user, CreateUser)
    print('AD user payload creation test passed (/)')
    
    oidc_user = users.make_oidc_user(first_name='test', last_name='test', email='email@email.com', login='oidc.login', oidc_id=5)
    assert isinstance(oidc_user, CreateUser)
    print('OIDC user creation test passed (/)')

    update = users.make_user_update(first_name='test')
    assert isinstance(update, UpdateUser)
    print('User update payload creation test passed (/)')

    auth = users.make_auth_data(method='openid')
    assert isinstance(auth, UserAuthData)
    print('User auth data payload creation test passed (/)')
    

    user_list = await users.get_users()
    assert isinstance(user_list, UserList)
    print('Getting users test passed (/)')
    print(f'Fetched {user_list.range.total} users')

    local_user = users.make_local_user(first_name='test', last_name='test', email='email@email.com')

    user = await users.create_user(local_user)
    assert isinstance(user, UserData)
    print('Local user creation test passed (/)')

    res = await users.delete_user(user.id)

    assert res == None
    print('User deletion passed (/)')

    oidc_user_res = await users.create_user(oidc_user)
    ad_user_res = await users.create_user(ad_user)

    assert isinstance(oidc_user_res, UserData)
    print('OIDC user creation passed (/)')
    assert isinstance(ad_user_res, UserData)
    print('AD user creation passed (/)')

    user_details = await users.get_user(user_id=oidc_user_res.id)
    assert isinstance(user_details, UserData)
    print('Getting user passed (/)')

    user_update = users.make_user_update(first_name='Test123')

    updated_user = await users.update_user(user_id=ad_user_res.id, user_update=user_update)

    assert isinstance(updated_user, UserData)
    assert updated_user.firstName == 'Test123'
    print('User update passed (/)')

    user_groups = await users.get_user_groups(user_id=oidc_user_res.id)

    assert isinstance(user_groups, UserGroupList)
    assert len(user_groups.items) == 0

    print('Getting user groups passed (/)')

    user_last_admin_rooms = await users.get_user_last_admin_rooms(user_id=ad_user_res.id)
    assert isinstance(user_last_admin_rooms, LastAdminUserRoomList)
    assert len(user_last_admin_rooms.items) == 0

    print('Getting last admin rooms passed (/)')

    user_roles = await users.get_user_roles(user_id=oidc_user_res.id)
    assert isinstance(user_roles, RoleList)

    print('Getting user roles passed (/)')

    user_attributes = await users.get_user_attributes(user_id=oidc_user_res.id)
    assert isinstance(user_attributes, AttributesResponse)

    print('Getting user attributes passed (/)')

    user_attribute_payload = users.make_custom_user_attribute(key='test', value='test')
    user_attribute_payload2 = users.make_custom_user_attribute(key='test2', value='test2')
    attribute_list = [user_attribute_payload, user_attribute_payload2]

    assert isinstance(user_attribute_payload, AttributeEntry)

    print('Creating user attribute payload passed (/)')

    attributes_update = users.make_attributes_update(list=attribute_list)

    assert isinstance(attributes_update, UpdateUserAttributes)

    print('Creating attributes update payload passed (/)')

    attributes_update_res = await users.update_user_attributes(user_id=oidc_user_res.id, attributes=attributes_update)
    assert isinstance(attributes_update_res, UserData)

    print('Updating user attributes passed (/)')

    attr_del = await users.delete_user_attribute(user_id=oidc_user_res.id, key='test')

    assert attr_del == None

    await users.delete_user_attribute(user_id=oidc_user_res.id, key='test2')

    await users.delete_user(user_id=oidc_user_res.id)
    await users.delete_user(user_id=ad_user_res.id)

    print('Users E2E tests passed (/)')



if __name__ == '__main__':
    asyncio.run(test_users_e2e())

    

   


