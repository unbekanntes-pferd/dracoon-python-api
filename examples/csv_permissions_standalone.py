""""
  Script to generate CSV files with all permissions per node 
  Outputs individual CSVs per room with permissions
  Usage: csv_permissions_standalone.py -p /your/output/path
  
  17.05.2022 Octavio Simone

"""

import argparse
import sys
from typing import List
from dracoon import DRACOON, OAuth2ConnectionType
import asyncio
import csv
from pathlib import Path

from dracoon.eventlog.responses import AuditNodeInfo, AuditNodeResponse


client_id = 'xxxxxxxxxxxxxxxxxxx'
client_secret = 'xxxxxxxxxxxxxxxxxxx'
base_url = "https://staging.dracoon.com"

# get all rooms
async def get_rooms(room_id: int, dracoon: DRACOON) -> List[AuditNodeInfo]:
  
  subroom_list = await dracoon.eventlog.get_rooms(parent_id=room_id, offset=0)
  
  if subroom_list.range.total > 500:
    # collect all items if more than 500 (requests)
    subroom_reqs = [dracoon.eventlog.get_rooms(parent_id=room_id, offset=offset) for offset in range(500, subroom_list.range.total, 500)]
    for batch in dracoon.batch_process(subroom_reqs):
      responses = await asyncio.gather(*batch)
      for response in responses:
        if "items" in response:
            subroom_list.items.extend(response.items)
            
  for subroom in list(subroom_list.items):
    subrooms = await get_rooms(room_id=subroom.nodeId, dracoon=dracoon)
    subroom_list.items.extend(subrooms)
    
  return subroom_list.items
            
  
# get room permissions
async def get_room_permissions(room_id: int, dracoon: DRACOON) -> List[AuditNodeResponse]:
  permissions = await dracoon.eventlog.get_permissions(filter=f'nodeParentId:eq:{str(room_id)}', raise_on_err=True)

  return permissions


def create_csv(permissions: List[AuditNodeResponse], path: str):
  
  if len(permissions) < 1:
    raise ValueError('No content.')
  
  if len(permissions[0].auditUserPermissionList) < 1:
    raise ValueError('No content.')
  
  if path[-1] == '/' or path[-1] == '\\':
    path = path[:-1]
    
  path = path.replace('\\', '/')
  

  file_path = f'{path}/{permissions[0].nodeId}_{permissions[0].nodeName}.csv'
  with open(file_path, 'w', encoding='utf-8') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['roomId', 'roomName', 'path', 'userId', 'firstName', 'lastName', 'login', 'manage', 'read', 'create', 'change', 'delete', 
                          'manageShares', 'manageFileRequests', 'readRecycleBin', 'restoreRecycleBin', 'deleteRecycleBin'])
      
    for permission in permissions[0].auditUserPermissionList:
      csv_writer.writerow([permissions[0].nodeId, permissions[0].nodeName, permissions[0].nodeParentPath, permission.userId,
                           permission.userFirstName, permission.userLastName, permission.userLogin, 
                           permission.permissions.manage, permission.permissions.read, permission.permissions.create,
                           permission.permissions.change, permission.permissions.delete, permission.permissions.manageDownloadShare, permission.permissions.manageUploadShare, 
                           permission.permissions.readRecycleBin, permission.permissions.restoreRecycleBin, permission.permissions.deleteRecycleBin]) 

      
# parse CLI arguments 
def parse_arguments() -> str:
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", required=True, help="Path to store CSV files with permissions")

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
  dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True, log_stream=True)
  print(dracoon.get_code_url())
  auth_code = input("Enter auth code: ")
  await dracoon.connect(connection_type=OAuth2ConnectionType.auth_code, auth_code=auth_code)
  room_list = await get_rooms(room_id=0, dracoon=dracoon)
  
  for room in room_list:
    permissions = await get_room_permissions(room_id=room.nodeId, dracoon=dracoon)
    try:
      create_csv(permissions=permissions, path=path)
    except ValueError:
      print(f"failed here: {room.nodeName}")
      continue
  
if __name__ == '__main__':
    asyncio.run(main())