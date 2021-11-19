"""
Example script showing the new async API: create rooms for users with given internal domain

18.11.2021 Octavio Simone

"""


from dracoon import DRACOON, OAuth2ConnectionType
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    PARENT_ID = 9999

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    username = 'username'
    password = 'topsecret' # use getpass.getpass() in interactive scripts

    connection = await dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
    
    # filter for users with specific domain
    user_filter = 'isGranted:eq:any|user:cn:test_oct_'
        
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

    room_tasks = []
        
        # create room for user if no room present
    for user in user_list:


        if user["hasRoom"] == False:
            name = f"{user['user'].userInfo.id}_{user['user'].userInfo.firstName}_{user['user'].userInfo.lastName}"
            admin_ids = [dracoon.user_info.id]

        room = dracoon.nodes.make_room(name=name, admin_ids=admin_ids, inherit_perms=False, parent_id=PARENT_ID)

        room_res = dracoon.nodes.create_room(room)
        room_tasks.append(room_res)

    for i in range(0, len(room_tasks) + 2, 2):
        rooms = await asyncio.gather(*room_tasks[i:i + 2])

        # create sub rooms (inherit perms)
        for room in rooms:
        
            mail_name = "email-attachment"
            mail_room = dracoon.nodes.make_room(name=mail_name, inherit_perms=True, parent_id=room.id)

            mail_res = await dracoon.nodes.create_room(mail_room)

            # create sub folders in sub room 
            in_folder = dracoon.nodes.make_folder(name="in", parent_id=mail_res.id)
            out_folder = dracoon.nodes.make_folder(name="out", parent_id=mail_res.id)
                
            in_res = dracoon.nodes.create_folder(in_folder)
            out_res = dracoon.nodes.create_folder(out_folder)

            folders = await asyncio.gather(in_res, out_res)

            for user in user_list:
                if room.name == f"{user['user'].userInfo.id}_{user['user'].userInfo.firstName}_{user['user'].userInfo.lastName}":

                    perms = dracoon.nodes.make_permissions(manage=False, create=True, read=True, change=True, delete=True, manage_shares=True, manage_file_requests=True, 
                                                            read_recycle_bin=True, restore_recycle_bin=True, delete_recycle_bin=True)
                    update = dracoon.nodes.make_permission_update(id=user['user'].userInfo.id, permission=perms)

                payload = {"items": [update]}

                assignment = await dracoon.nodes.update_room_users(room_id=room.id, users_update=payload)


if __name__ == '__main__':
    asyncio.run(main())