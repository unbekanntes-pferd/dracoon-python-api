# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Create personal rooms for all users matching an email part
# Requires dracoon package
# Author: Octavio Simone, 20.11.2020
# ---------------------------------------------------------------------------#

from dracoon import core, users, nodes
import sys
import getpass
import csv
import os

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# parent ID of room for personal rooms (user running script must be room admin)
parentID = 99 # replace with own node id

# create DRACOON object
my_dracoon = core.Dracoon(clientID, clientSecret)
my_dracoon.set_URLs(baseURL)

# get user login credentials (basic, AD possible)
RO_user = input('Username: ')
RO_password = getpass.getpass('Password: ')

# try to authenticate - exit if request fails (timeout, connection error..)
try:
    login_response = my_dracoon.basic_auth(RO_user, RO_password)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

# authenticate or exit if authentication fails
if login_response.status_code == 200:
    print('Login successful: ' + str(login_response.status_code))
else:
    print(login_response.status_code)
    if login_response.json()["error"] and login_response.json()["error_description"]:
        print(login_response.json()["error"])
        print(login_response.json()["error_description"])
    else:
        print(login_response.text)
    sys.exit()  # exit script if login not successful

# optional: provide specific filter
f = 'isGranted:eq:any|user:cn:@octsim.com'


# create list for users
user_list = []

# generate request to get users - filter can be omitted, default is no filter
r = nodes.get_room_users(nodeID=parentID, offset=0, filter=f)
# perform request with authenticated DRACOON instance
try:
    user_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

# if call successful, check if user count exceeds 500 and fill list
if user_response.status_code == 200:
    total_users = user_response.json()["range"]["total"]
    for user in user_response.json()['items']:
        user_list.append(user)
    print('Added users to list.')
    print(f'User count: {total_users}')
    if total_users > 500:
        for offset in range(500, total_users, 500):
            r = nodes.get_room_users(nodeID=parentID, offset=offset, filter=f)
            try:
                user_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            for user in user_response.json()['items']:
                user_list.append(user)
else:
    print(f'Error: {user_response.status_code}')
    print(f'Details: {user_response.text}')

# create request to get search for all rooms in a parent room
r = nodes.get_nodes(roomManager='true', parentID=parentID, offset=0, filter='type:eq:room')

try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

room_list = []

# get all rooms in parent room 
if room_response.status_code == 200:
    total_rooms = room_response.json()["range"]["total"]
    for room in room_response.json()["items"]:
        room_list.append(room)
    print('Added rooms to list.')
    print(f'Room count: {total_rooms}')
    if total_rooms > 500:
        for offset in range(500, total_users, 500):
            r = nodes.get_nodes(roomManager='true', parentID=parentID, offset=offset, filter='type:eq:room')
            try:
                room_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            for room in room_response.json()['items']:
                room_list.append(room)
    
# check for each user if a room exists
    for room in room_list:
        for user in user_list:
            if room["name"] == f'{user["userInfo"]["id"]}_{user["userInfo"]["firstName"]}_{user["userInfo"]["lastName"]}':
                user["hasRoom"] = True

# create room for each user in list

for user in user_list:

    # check if room was found - only crate room if no room present 
    if "hasRoom" not in user:
        params = {
            "name": f"{user['userInfo']['id']}_{user['userInfo']['firstName']}_{user['userInfo']['lastName']}",
            "adminIds": [user['userInfo']['id']],
            "parentId": parentID,
            "inheritPermissions": False
        }

        # create request for room creation with name and parent path
        # try to create a room
        r = nodes.create_room(params)
        try:
            room_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # respond to creation request
        if room_response.status_code == 201:
            room_id = room_response.json()["id"]
            print(
                f'Room {user["userInfo"]["id"]}_{user["userInfo"]["firstName"]}_{user["userInfo"]["lastName"]} created.')
        else:
            print('Room not created.')
            print(f'Details: {room_response.text}')
            continue
