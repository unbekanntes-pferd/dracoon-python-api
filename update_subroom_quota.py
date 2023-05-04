"""
Update Quota to QUOTA (in Byte) of all Top-Level Rooms within certain PARENT_ID
04.05.2023 Quirin Wierer
"""

from dracoon import DRACOON
import asyncio

from dracoon.nodes.models import UpdateRoom
 
async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXX'
    PARENT_ID = 12345
    QUOTA = 10737418240 #10GB
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)
    
    #get all managable rooms
    rooms = await dracoon.nodes.get_nodes(room_manager=True, parent_id=PARENT_ID, filter='type:eq:room', raise_on_err=True)
    room_list=[*rooms.items]
    if rooms.range.total > 500:
        for offset in range(500,rooms.range.total,500):
            rooms = await dracoon.nodes.get_nodes(room_manager=True, parent_id=PARENT_ID, filter='type:eq:room', offset=offset, raise_on_err=True)
            room_list=[*rooms.items]

    #update room quotas
    for room in room_list:
        payload = UpdateRoom(quota = QUOTA)
        print(room.id , room.name)
        await dracoon.nodes.update_room(node_id=room.id, room_update=payload, raise_on_err=True)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())
