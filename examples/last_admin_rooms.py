""""
  Script to find last admin rooms
  01.08.2022 Quirin Wierer

"""

import argparse
import sys
from typing import List
from dracoon import DRACOON, OAuth2ConnectionType
import asyncio
import csv

from dracoon.eventlog.responses import AuditNodeInfo, AuditNodeResponse, AuditUserPermission

# client_id = 'XXXXXXXXXXXXXXXX'
# client_secret = 'XXXXXXXXXXXXXXXX'
# base_url = 'https://dracoon.team'
# user_id = 9999999999
# file_path = "./"

#credentials
base_url = 'https://demo-qw.dracoon.com'
client_id = '1pi0pNw9RLEJOqXOKfBx36R3vHW7lKrO'
client_secret = 'unXiTL3us8rOQdzvtkoIb7UMUgdmEtFo'
user_id = 1
file_path = "./"

def create_csv(permissions: List, path: str):
  
  file_name = f'{file_path}/Last_admin_rooms_of_user_{user_id}.csv'
  with open(file_name, 'w', encoding='utf-8') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['nodeId', 'nodeName', 'parentNodePath'])
      
    for permission in range(len(permissions)):
      csv_writer.writerow(permissions[permission]) 



async def main():
  
  dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True, log_stream=False)
  print(dracoon.get_code_url())
  auth_code = input("Enter auth code: ")
  await dracoon.connect(connection_type=OAuth2ConnectionType.auth_code, auth_code=auth_code)

# retrieve datarooms with permission manage
  room_list = await dracoon.eventlog.get_permissions(filter=f'userId:eq:{str(user_id)}|permissionsManage:eq:true', raise_on_err=True)

#check for more than 500 rooms
  while len(room_list) == 500:
    offset = 500
    offset_room_list = await dracoon.eventlog.get_permissions(filter=f'userId:eq:{str(user_id)}', offset= offset, raise_on_err=True)
    offset = offset+500
    room_list.extend(offset_room_list)

#find datarooms where only 1 admin
  last_admin_rooms = []
  for room in room_list:
    all_room_managers= await dracoon.eventlog.get_permissions(filter=f'nodeId:eq:{str(room.nodeId)}|permissionsManage:eq:true', raise_on_err=True)
    for managers in all_room_managers:
        if len(managers.auditUserPermissionList) ==1:
            for user in managers.auditUserPermissionList:
                parentId = managers.nodeParentId
                parentNodePath = managers.nodeParentPath

                room_list = []
                room_list.append(managers.nodeId)
                room_list.append(managers.nodeName)
                #room_list.append(managers.nodeParentId)
                room_list.append(parentNodePath)
                last_admin_rooms.append(room_list)

  create_csv(last_admin_rooms, file_path)

if __name__ == '__main__':
    asyncio.run(main())