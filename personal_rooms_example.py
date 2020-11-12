# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Create personal rooms for all users matching an email, delete all 
# previously existing rooms before
# Requires dracoon package
# Author: Octavio Simone, 12.11.2020
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
parentID = 6847

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
f = 'email:cn:@octsim.com'


# create list for users
user_list = []

# generate request to get users - filter can be omitted, default is no filter
r = users.get_users(offset=0, filter=f)
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
            r = users.get_users(offset=offset, filter=f)
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



if room_response.status_code == 200:
    total_rooms = room_response.json()["range"]["total"]
    room_list = room_response.json()["items"]
    print(room_list)
    print(room_response.text)
    if total_rooms > 500:
        for offset in range(500, total_users, 500):
            r = nodes.get_nodes(roomManager='true', parentID=parentID, offset=offset, filter='type:eq:room')
            try:
                room_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            for room in room_response.json()['items']:
                room_list.append(user)
else:
    e = f'Error getting folders - details: {room_response.text}'
    raise SystemExit(e)

# get all room ids
room_id_list = []

print(len(room_id_list))

for room in room_list:
    room_id_list.append(room["id"])

# create request to delete a room
r = nodes.delete_nodes(room_id_list)

# only send request to delete rooms if rooms present
if len(room_id_list) > 0:
    room_delete_response = my_dracoon.delete(r)
    if room_delete_response.status_code == 204:
        print(f"{len(room_id_list)} rooms deleted.")
    else:
        e = f'Error deleting rooms - details: {room_delete_response.text}'
        raise SystemExit(e)


# create room for each user in list

for user in user_list:
    params = {
        "name": f"{user['id']}_{user['firstName']}_{user['lastName']}",
        "adminIds": [user['id']],
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
        room_list.append(room_id)
        print(
            f'Room {user["id"]}_{user["firstName"]}_{user["lastName"]} created.')
    else:
        print('Room not created.')
        print(f'Details: {room_response.text}')
        continue
