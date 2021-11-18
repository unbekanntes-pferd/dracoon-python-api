"""
Example script showing the new async API: create rooms for users with given internal domain

04.11.2021 Octavio Simone

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
    filter = 'isGranted:eq:any|user:cn:@yourdomain.com'
    
    # get users
    user_res = await dracoon.nodes.get_room_users(node_id=PARENT_ID, filter=filter)
    
    total_users = user_res.json()["range"]["total"]
    user_list = user_res.json()["items"]
    
    # get all available users
    if total_users > 500:
        for offset in range(500, total_users, 500):
            user_res = await dracoon.nodes.get_room_users(node_id=PARENT_ID, filter=filter, offset=offset)
            for user in user_res.json()["items"]:
                user_list.append(user)
    
    # get all rooms in parent ("Home")
    room_res = await dracoon.nodes.get_nodes(room_manager=True, parent_id=PARENT_ID, filter='type:eq:room')
    room_list = room_res.json()["items"]
    total_rooms = room_res.json()["range"]["total"]
    
    # get all rooms (> 500 items)
    if total_rooms > 500:
        for offset in range(500, total_rooms, 500):
            room_res = await dracoon.nodes.get_nodes(room_manager=True, node_id=PARENT_ID, filter='type:eq:room', offset=offset)
            for room in room_res.json()["items"]:
                room_list.append(room)
    
    # check if room exists, set flag 
    for room in room_list:
        for user in user_list: 
            if room["name"] == f'{user["userInfo"]["id"]}_{user["userInfo"]["firstName"]}_{user["userInfo"]["lastName"]}':
                user["hasRoom"] = True
    
    # create room for user if no room present
    for user in user_list:

        if "hasRoom" not in user:
            name = f"{user['userInfo']['id']}_{user['userInfo']['firstName']}_{user['userInfo']['lastName']}"
            admin_ids = [user['userInfo']['id']]

            room = dracoon.nodes.make_room(name=name, admin_ids=admin_ids, inherit_perms=False, parent_id=PARENT_ID)

            room_res = await dracoon.nodes.create_room(room)
            if room_res.status_code == 201:
                print(f"Room for {user['userInfo']['email']} created.")
    
    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())