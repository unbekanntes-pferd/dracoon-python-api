"""
Updating new_group_member_acceptance for all datarooms within a parent node
18.11.2021 Quirin Wierer
"""

from dracoon import DRACOON
import asyncio

from dracoon.nodes_models import ProcessRoomPendingUsers, UpdateRoomGroups
from dracoon.nodes_responses import RoomGroup
 
async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
    PARENT_ID = XXX
    GROUP_ID = XXX

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)
    
    # retrieve datarooms (all in tree)
    rooms = await dracoon.nodes.search_nodes(search = "*", filter="type:eq:room", parent_id=PARENT_ID, depth_level=-1)
    room_ids = [room.id for room in rooms.items]
 
    #retrive room rights from parent room
    filter = "effectivePerm:eq:true|groupId:eq:" + str(GROUP_ID)
    room_group_list = await dracoon.nodes.get_room_groups(room_id = PARENT_ID, filter=filter)

    payload = UpdateRoomGroups(items = room_group_list.items)
    #update room group permissions
    for room in rooms.items:
        await dracoon.nodes.update_room_groups(room_id=room.id, groups_update=payload, raise_on_err=True)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())
