
from dracoon.groups import DRACOONGroups
from dracoon import DRACOONClient, OAuth2ConnectionType
import dotenv
import os
import asyncio
from dracoon.groups.models import CreateGroup, UpdateGroup

from dracoon.groups.responses import Group, GroupList, GroupUserList, LastAdminGroupRoomList
from dracoon.user.responses import RoleList

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
USER_ID = 795 # replace with existing user id

async def test_groups_e2e():

    dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    groups = DRACOONGroups(dracoon_client=dracoon)
    assert isinstance(groups, DRACOONGroups)
    print('Connection test complete (/)')


    group_list = await groups.get_groups()
    assert isinstance(group_list, GroupList)
    print('Getting user list test passed (/)')

    new_group = groups.make_group(name='THIS IS A TEST')
    assert isinstance(new_group, CreateGroup)

    print('Making group create payload test passed (/)')

    group = await groups.create_group(new_group)
    assert isinstance(group, Group)

    print('Creating a group test passed (/)')

    update = groups.make_group_update(name='THIS IS ANOTHER TEST')
    assert isinstance(update, UpdateGroup)

    print('Making group update payload test passed (/)')

    updated_group = await groups.update_group(group_id=group.id, group_update=update)
    assert updated_group.name == 'THIS IS ANOTHER TEST'
    print('Updating a group test passed (/)')

    group_roles = await groups.get_group_roles(group_id=group.id)
    assert isinstance(group_roles, RoleList)
    print('Getting group roles test passed (/)')

    group_last_admin_rooms = await groups.get_group_last_admin_rooms(group_id=group.id)
    assert isinstance(group_last_admin_rooms, LastAdminGroupRoomList)
    print('Getting group last admin rooms test passed (/)')
    
    user_list = [USER_ID]
    add_user = await groups.add_group_users(group_id=group.id, user_list=user_list)
    assert isinstance(add_user, Group)
    print('Adding user to group test passed (/)')

    group_users = await groups.get_group_users(group_id=group.id)
    assert isinstance(group_users, GroupUserList)
    assert len(group_users.items) > 0
    assert group_users.items[0].userInfo.id == USER_ID
    print('Getting group users test passed (/)')

    del_group_user = await groups.delete_group_users(group_id=group.id, user_list=user_list)
    assert isinstance(del_group_user, Group)
    print('Deleting group users test passed (/)')

    del_group = await groups.delete_group(group_id=group.id)

    assert del_group == None

    print('Deleting group test passed (/)')

    print('Groups E2E tests passed (/)')



if __name__ == '__main__':
    asyncio.run(test_groups_e2e())

    

   


