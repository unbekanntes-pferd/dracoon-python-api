"""
Example script showing the new async API: create rooms for users with given internal domain

18.11.2021 Octavio Simone

"""


from dracoon import DRACOON
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    PARENT_ID = 9999

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    print(dracoon.get_code_url())
    auth_code = input("Please enter auth code: ")

    connection = await dracoon.connect(auth_code=auth_code)
    
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
            # create home room
            name = f"{user['user'].userInfo.id}_{user['user'].userInfo.firstName}_{user['user'].userInfo.lastName}"
            admin_ids = [user['user'].userInfo.id, dracoon.user_info.id]
            room = dracoon.nodes.make_room(name=name, admin_ids=admin_ids, inherit_perms=False, parent_id=PARENT_ID)
           
            room_res = await dracoon.nodes.create_room(room)
            
            # create sub room for OAI
            mail_name = "DRACOON for Outlook"
            mail_room = dracoon.nodes.make_room(name=mail_name, inherit_perms=True, parent_id=room_res.id)

            mail_res = await dracoon.nodes.create_room(mail_room)

            # create sub folders in sub room 
            in_folder = dracoon.nodes.make_folder(name="Inbox", parent_id=mail_res.id)
            out_folder = dracoon.nodes.make_folder(name="Outbox", parent_id=mail_res.id)
                        
            in_res = dracoon.nodes.create_folder(in_folder)
            out_res = dracoon.nodes.create_folder(out_folder)

            folders = await asyncio.gather(in_res, out_res)
            
            # remove admin perms for admin user
            no_perm = dracoon.nodes.make_permissions(False, False, False, False, False, False, False, False, False, False)
            perms_update = dracoon.nodes.make_permission_update(id=dracoon.user_info.id, permission=no_perm)
            update = {"items": [perms_update]}

            remove_perms = await dracoon.nodes.update_room_users(room_id=room_res.id, users_update=update)


if __name__ == '__main__':
    asyncio.run(main())