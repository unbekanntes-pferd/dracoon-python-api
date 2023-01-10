"""
homeroom creation: create rooms for users with given internal domain with admin access via group

30.05.2022 Quirin Wierer

"""


from dracoon import DRACOON, OAuth2ConnectionType
import asyncio
import os

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
    password = os.environ.get("env_variable_name")
    username = 'testadmin'
    PARENT_ID = 99999
    ADMIN_GROUP_ID = 99999
    # filter for users with specific domain
    user_filter = 'isGranted:eq:any|user:cn:XignIn'


    #establish connection
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    connection = await dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
        
    # get users
    user_res = await dracoon.nodes.get_room_users(room_id=PARENT_ID, filter=user_filter)
    total_users = user_res.range.total
    user_list = [{"user": user, "hasRoom": False} for user in user_res.items ]
        
    # get all available users
    if total_users > 500:
        for offset in range(500, total_users, 500):
            user_res = await dracoon.nodes.get_room_users(node_id=PARENT_ID, filter=user_filter, offset=offset)
            for user in user_res.items:
                user_p = {
                            "user": user,
                            "hasRoom": False
                        }
                user_list.append(user_p)

    room_filter = 'type:eq:room'
        
    # get all rooms in parent ("Home")
    room_res = await dracoon.nodes.get_nodes(room_manager=True, parent_id=PARENT_ID, filter=room_filter)
    room_list = room_res.items
    total_rooms = room_res.range.total
        
    # get all rooms (> 500 items)
    if total_rooms > 500:
        for offset in range(500, total_rooms, 500):
            room_res = await dracoon.nodes.get_nodes(room_manager=True, node_id=PARENT_ID, filter=room_filter, offset=offset)
            for room in room_res.items:
                room_list.append(room)
        
    # check if room exists, set flag 
    for room in room_list:
        for user in user_list:
            if room.name == f"{user['user'].userInfo.id}_{user['user'].userInfo.firstName}_{user['user'].userInfo.lastName}":
                user["hasRoom"] = True
        
    # create room for user if no room present
    for user in user_list:

        if user["hasRoom"] == False:
            # create home room
            name = f"{user['user'].userInfo.id}_{user['user'].userInfo.firstName}_{user['user'].userInfo.lastName}"
            #admin_ids = [user['user'].userInfo.id, dracoon.user_info.id]
            room = dracoon.nodes.make_room(name=name, admin_group_ids=[ADMIN_GROUP_ID], inherit_perms=False, parent_id=PARENT_ID)
           
            room_res = await dracoon.nodes.create_room(room)

            # set edit perms for user
            no_admin_perm = dracoon.nodes.make_permissions(False, True, True, True, True, True, True, True, True, False)
            perms_update = dracoon.nodes.make_permission_update(id=user['user'].userInfo.id, permission=no_admin_perm)
            update = {"items": [perms_update]}

            add_perms = await dracoon.nodes.update_room_users(room_id=room_res.id, users_update=update)
        
           
if __name__ == '__main__':
    asyncio.run(main())