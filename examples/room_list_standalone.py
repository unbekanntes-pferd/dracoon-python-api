""""
  Script to generate CSV file with all rooms  
  Outputs a CSV with node info for all rooms
  Usage: csv_room_list_standalone.py -p /your/output/path
  
  23.08.2022 Octavio Simone

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
base_url = "https://your-dracoon.domain.com"

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
  permissions = await dracoon.eventlog.get_permissions(filter=f'nodeId:eq:{str(room_id)}', raise_on_err=True)

  return permissions

def create_csv(permissions: List[List[AuditNodeResponse]], path: str):
  
  if len(permissions) < 1:
    raise ValueError('No content.')
  
  # remove trailing slash
  if path[-1] == '/' or path[-1] == '\\':
    path = path[:-1]
    
  # handle Windows paths
  path = path.replace('\\', '/')
  
  file_path = f'{path}/room_list.csv'
  with open(file_path, 'w', encoding='utf-8') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['roomId', 'roomName', 'path', 'countChildren', 'size', 'quotaUsed', 'isEncrypted', 'recycleBinRetention'])
      
    for permission in permissions:
      node_info = permission[0]
      csv_writer.writerow([node_info.nodeId, node_info.nodeName, node_info.nodeParentPath, node_info.nodeCntChildren, 
                           node_info.nodeSize, node_info.nodeQuota, node_info.nodeIsEncrypted, node_info.nodeRecycleBinRetentionPeriod])
      
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
  node_info_list = []
  
  for room in room_list:
    permissions = await get_room_permissions(room_id=room.nodeId, dracoon=dracoon)
    node_info_list.append(permissions)
  try:
    create_csv(permissions=node_info_list, path=path)
  except ValueError:
    print(f"Creating CSV failed - no content.")

  
if __name__ == '__main__':
    asyncio.run(main())