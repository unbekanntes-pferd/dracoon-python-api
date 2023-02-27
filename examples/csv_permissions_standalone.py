""""
  Script to generate CSV files with all permissions of all the top level room and its child rooms
  Outputs individual CSVs per room with permissions
  Usage: csv_permissions_standalone.py -p /your/output/path
  
  27.02.2023 Octavio Simone & Ralf Boehler
  
"""

import argparse
import sys
import asyncio
import csv
from typing import List
from pathlib import Path
from pydantic import BaseModel

from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.eventlog.responses import AuditNodeInfo, AuditNodeResponse


client_id = 'xxxxxxxxxxxxxxxxxxx'
client_secret = 'xxxxxxxxxxxxxxxxxxx'
base_url = "https://demo.dracoon.com"

class TopLevelWithSubRooms(BaseModel):
    parentRoom: AuditNodeInfo
    subRooms: list[AuditNodeInfo]


class TopLevelRooms(BaseModel):
    rooms: list[TopLevelWithSubRooms]


# get all rooms
async def get_rooms(room_id: int, dracoon: DRACOON) -> List[AuditNodeInfo]:
    topLevelRooms = TopLevelRooms(rooms=[])

    topLevelRoom_list = await dracoon.eventlog.get_rooms(parent_id=room_id, offset=0)

    if topLevelRoom_list.range.total > 500:
        # collect all items if more than 500 (requests)
        subroom_reqs = [dracoon.eventlog.get_rooms(
            parent_id=room_id, offset=offset) for offset in range(500, topLevelRoom_list.range.total, 500)]
        for batch in dracoon.batch_process(subroom_reqs):
            responses = await asyncio.gather(*batch)
            for response in responses:
                if "items" in response:
                    topLevelRoom_list.items.extend(response.items)

    for topLevelRoom in list(topLevelRoom_list.items):
        topLevelRoom = TopLevelWithSubRooms(
            parentRoom=topLevelRoom, subRooms=[])
        topLevelRooms.rooms.append(topLevelRoom)

    for index, room in enumerate(topLevelRooms.rooms):

        subrooms = await get_sub_rooms(room_id=room.parentRoom.nodeId, dracoon=dracoon)
        topLevelRooms.rooms[index].subRooms = subrooms

    return topLevelRooms


# get room permissions
async def get_sub_rooms(room_id: int, dracoon: DRACOON) -> List[AuditNodeInfo]:

    subroom_list = await dracoon.eventlog.get_rooms(parent_id=room_id, offset=0)

    if subroom_list.range.total > 500:
        # collect all items if more than 500 (requests)
        subroom_reqs = [dracoon.eventlog.get_rooms(
            parent_id=room_id, offset=offset) for offset in range(500, subroom_list.range.total, 500)]
        for batch in dracoon.batch_process(subroom_reqs):
            responses = await asyncio.gather(*batch)
            for response in responses:
                if "items" in response:
                    subroom_list.items.extend(response.items)

    for subroom in list(subroom_list.items):
        subrooms = await get_sub_rooms(room_id=subroom.nodeId, dracoon=dracoon)
        subroom_list.items.extend(subrooms)

    return subroom_list.items


async def get_room_permissions(room_id: int, dracoon: DRACOON) -> List[AuditNodeResponse]:
    permissions = await dracoon.eventlog.get_permissions(filter=f'nodeId:eq:{str(room_id)}', raise_on_err=True)

    return permissions


def create_csv(permissions: List[AuditNodeResponse], path: str):

    if len(permissions) < 1:
        raise ValueError('No content.')

    if path[-1] == '/' or path[-1] == '\\':
        path = path[:-1]

    path = path.replace('\\', '/')

    file_path = f'{path}/{permissions[0].nodeId}_{permissions[0].nodeName}.csv'
    with open(file_path, 'w', encoding='utf-8') as f:
        csv_writer = csv.writer(f, delimiter=';')
        csv_writer.writerow(['roomId', 'roomName', 'path','parentId', 'userId', 'firstName', 'lastName', 'login', 'manage', 'read', 'create', 'change', 'delete',
                             'manageShares', 'manageFileRequests', 'readRecycleBin', 'restoreRecycleBin', 'deleteRecycleBin'])

    for node in permissions:
        with open(file_path, 'a', encoding='utf-8') as f:
          csv_writer = csv.writer(f, delimiter=';')     
          if len(node.auditUserPermissionList) == 0:
              csv_writer.writerow([node.nodeId, node.nodeName, node.nodeParentPath, node.nodeParentId, '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-', '-'])
          
          else:
            for permission in node.auditUserPermissionList:

                csv_writer.writerow([node.nodeId, node.nodeName, node.nodeParentPath,node.nodeParentId, permission.userId,
                                    permission.userFirstName, permission.userLastName, permission.userLogin,
                                    permission.permissions.manage, permission.permissions.read, permission.permissions.create,
                                    permission.permissions.change, permission.permissions.delete, permission.permissions.manageDownloadShare, permission.permissions.manageUploadShare,
                                    permission.permissions.readRecycleBin, permission.permissions.restoreRecycleBin, permission.permissions.deleteRecycleBin])


# parse CLI arguments
def parse_arguments() -> str:
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", required=True,
                    help="Path to store CSV files with permissions")

    args = vars(ap.parse_args())

    # if no path is given, exit
    if args["path"] is None:
        print("Providing a path is mandatory.")
        sys.exit(1)

    path = args['path']

    target_folder = Path(path)

    if not target_folder.is_dir():
        print("Provided path is not a valid directory.")
        sys.exit(1)

    return path


async def main():

    path = parse_arguments()
    dracoon = DRACOON(base_url=base_url, client_id=client_id,
                      client_secret=client_secret, raise_on_err=True, log_stream=True)
    print(dracoon.get_code_url())
    auth_code = input("Enter auth code: ")
    await dracoon.connect(connection_type=OAuth2ConnectionType.auth_code, auth_code=auth_code)
    parent_room_list = await get_rooms(room_id=0, dracoon=dracoon)

    for parent_room in parent_room_list.rooms:
        permissions_per_top_level_room = []

        permissions = await get_room_permissions(room_id=parent_room.parentRoom.nodeId, dracoon=dracoon)
        permissions_per_top_level_room.extend(permissions)

        for sub_room in parent_room.subRooms:
            sub_room_permissions = await get_room_permissions(room_id=sub_room.nodeId, dracoon=dracoon)
            permissions_per_top_level_room.extend(sub_room_permissions)

        try:
            create_csv(permissions=permissions_per_top_level_room, path=path)
        except ValueError:
            print(f"failed here: {parent_room.parentRoom.nodeName}")
            continue
        

if __name__ == '__main__':
    asyncio.run(main())
