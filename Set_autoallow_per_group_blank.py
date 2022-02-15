
"""
Example script showing the new async API with processing all pending assignments
18.11.2021 Octavio Simone
"""

from dracoon import DRACOON
import asyncio
import logging

from dracoon.nodes_models import ProcessRoomPendingUsers

async def main():
    baseURL = 'XXX'
    client_id = 'XXX'
    client_secret = 'XXX'

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret, log_level=logging.DEBUG)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)
    
    # retrieve pending assignments
    pending_assign = await dracoon.nodes.get_pending_assignments(filter="groupId:eq:X|state:eq:WAITING")

    assignments = {
      "items": []
    }
    
    # build assignment processing payload 
    for pending_assignment in pending_assign.items:

        assignment = {
        "roomId": pending_assignment.roomId,
        "roomName": pending_assignment.roomName,
        "userId": pending_assignment.userInfo.id,
        "groupId": pending_assignment.groupInfo.id,
        "state": "ACCEPTED"
      }

        assignments["items"].append(assignment)

    # ensure payload is correct 
    payload = ProcessRoomPendingUsers(**assignments)

    # send request
    pending_processed = await dracoon.nodes.process_pending_assignments(payload = True)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())