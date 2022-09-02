"""
Example script to import users, create personal rooms and assign them to a group
Usage: user_import_standalone.py -f yourimport.csv -p 999
-f / --file is a parameter for the CSV file 
Format:

firstName,lastName,email
IMPORTANT: header in CSV necessary, first line will be skipped

-p / --parent is a parameter for the node id of the parent room 
Provide a room where the user performing the script has admin permissions
If root, please use a room manager account.

02.09.2022 Octavio Simone 

"""



# std imports
import asyncio
from typing import Tuple
import sys
import argparse
import csv
from pathlib import Path

# pydanctic model
from pydantic import BaseModel

# DRACOON imports
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.groups.responses import Group
from dracoon.nodes.models import Node
from dracoon.user.responses import UserData, UserItem
from dracoon.errors import HTTPConflictError, HTTPUnauthorizedError, HTTPForbiddenError, DRACOONHttpError

# credentials 
client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
username = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
password = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
base_url = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

# group name
GROUP_NAME = 'The Foos'

class UserImport(BaseModel):
    first_name: str
    last_name: str
    email: str
    
    @property
    def room_name(self):
        return f"{self.first_name.lower()}.{self.last_name.lower()}"
    
def parse_csv(csv_file: str) -> list[UserImport]:
    """" parse a CSV and get users to import """
    
    user_list = []
    
    # open CSV file (example: import.csv in cwd)
    with open(csv_file, 'r') as f:
        csv_reader = csv.reader(f, delimiter=",", quoting=csv.QUOTE_ALL, quotechar='"')
        # skip header
        next(csv_reader)

        # csv format: 'firstName', 'lastName', 'email'
        for user in csv_reader:
            print(user)
            
            payload = {
                "first_name": user[0],
                "last_name": user[1],
                "email": user[2],
            }
                  
            parsed_user = UserImport(**payload)
            
            user_list.append(parsed_user)
            
        return user_list

# parse CLI arguments 
def parse_arguments() -> Tuple[str, int]:
    """ parse CLI arguments """
    
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="CSV file to parse – must contain first & last name and email address of a user.")
    ap.add_argument("-p", "--parent", required=True, help="Parent room id to create personal rooms for users on list.")
    args = vars(ap.parse_args())

    # if no file is given, exit
    if args["file"] is None:
        print("Providing a csv file is mandatory.")
        sys.exit(2)
    else:
        csv_file = args["file"]
        csv_path = Path(csv_file)
        if not csv_path.is_file():
            print(f"Invalid path: file does not exist ({csv_file})")
            sys.exit(2)
            

    if args["parent"] is None:
        print("Providing parent id for personal rooms is mandatory.")
        sys.exit(2)
    else:
        try:
            parent_id = int(args["parent"])
        except ValueError:
            print(f"Invalid id: {args['parent']} - parent id must be numeric.")
            sys.exit(2)
            
    return csv_file, parent_id

async def login(username: str, password: str) -> DRACOON:
    """ authenticate in DRACOON """
    dracoon = DRACOON(client_id=client_id, client_secret=client_secret, base_url=base_url, log_stream=True)
    try:
        await dracoon.connect(connection_type=OAuth2ConnectionType.password_flow, username=username, password=password)
        return dracoon
    except HTTPUnauthorizedError:
        dracoon.logger.error("Invalid credentials.")

async def get_user_list(dracoon: DRACOON) -> list[UserItem]:
    """ get list of current users """
    try:
        users_res = await dracoon.users.get_users(raise_on_err=True)
        user_list = users_res.items
        
        if users_res.range.total > 500:
            for offset in range(500, user_list.range.total, 500):
                users_res = await dracoon.users.get_users(offset=offset, raise_on_err=True)
                user_list.extend(users_res.items)           
        return user_list
    except HTTPForbiddenError:
        dracoon.logger.error("Insufficient rights: user manager permission required.")
        sys.exit(1)
    except DRACOONHttpError:
        dracoon.logger.error("An error ocurred getting users.")
        sys.exit(2)

def sync_user_list(csv_list: list[UserImport], user_list: list[UserItem]):
    """ remove all users from import list that already exist """
    for user in user_list:
        for index, import_user in enumerate(csv_list):
            if user.email == import_user.email:
                csv_list.pop(index)
                
    return csv_list
                
async def create_user(dracoon: DRACOON, first_name: str, last_name: str, email: str) -> UserData:
    """ create a local user """
    payload = dracoon.users.make_local_user(first_name=first_name, last_name=last_name, email=email)
    
    try:
        user = await dracoon.users.create_user(user=payload)
    except HTTPForbiddenError:
        dracoon.logger.error("Insufficient rights: user manager permission required.")
        await dracoon.logout()
        sys.exit(2)
    except HTTPConflictError:
        dracoon.logger.error(f"User already exists: {payload.email}.")
    except DRACOONHttpError:
        dracoon.logger.error("An error ocurred getting users.")
        await dracoon.logout()
        sys.exit(2)

    return user

async def create_personal_room(dracoon: DRACOON, user: UserData, name: str, parent_id: int) -> Node:
    """ create a personal room """
    
    if parent_id == 0:
        parent_id = None
    
    payload = dracoon.nodes.make_room(name=name, parent_id=parent_id, admin_ids=[user.id], inherit_perms=False)

    room = await dracoon.nodes.create_room(room=payload, raise_on_err=True)
    
    return room

async def get_group_by_name(dracoon: DRACOON, name: str) -> Group:
    """ get a group by name """
    group = await dracoon.groups.get_groups(filter=f'name:cn:{name}')
    
    if len(group.items) > 0:
        return group.items[0]
    else:
        return None
    
async def assign_to_group(dracoon: DRACOON, user: UserData, group_name: str):
    """ assign a user to a group """
    group = await get_group_by_name(dracoon=dracoon, name=group_name)
    
    if group is None:
        dracoon.logger.error("Group not found.")
        await dracoon.logout()
        sys.exit(2)
    
    try:
        assignment = await dracoon.groups.add_group_users(group_id=group.id, user_list=[user.id])
        return assignment
    except HTTPForbiddenError:
        dracoon.logger.error("Insufficient rights: group manager permission required.")
        await dracoon.logout()
    except DRACOONHttpError:
        dracoon.logger.error("An error ocurred getting users.")

async def main():
    """ 
    main script
    imports users from csv
    creates personal rooms
    assigns all users to same group
    """
    csv_file, parent_id = parse_arguments()
    
    import_list = parse_csv(csv_file=csv_file)
    
    dracoon = await login(username=username, password=password)
    user_list = await get_user_list(dracoon=dracoon)
    import_list = sync_user_list(csv_list=import_list, user_list=user_list)
    
    for user_import in import_list:
        user = await create_user(dracoon=dracoon, first_name=user_import.first_name, last_name=user_import.last_name, email=user_import.email)
            
        if not user:
            continue
        
        dracoon.logger.info(f"User {user.email} created.")   
        
        await assign_to_group(dracoon=dracoon, user=user, group_name=GROUP_NAME)  
        dracoon.logger.info("")
        
        room = await create_personal_room(dracoon=dracoon, user=user, name=user_import.room_name, parent_id=parent_id)
        dracoon.logger.info(f"Room {room.name} created.")
        
        
if __name__ == "__main__":
    asyncio.run(main())