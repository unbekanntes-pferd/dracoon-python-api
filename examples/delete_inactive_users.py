# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Delete inactive users and their personal rooms
# Requires dracoon package
# Author: Octavio Simone, 28.04.2021
# ---------------------------------------------------------------------------#

from dracoon import core, users, nodes
import sys
import getpass
from datetime import datetime

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

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

# parent ID of room for personal rooms (user running script must be room admin)
parentID = 7343 # replace with own node id

# interval (in days) for last login (users greater than interval will be deleted)
INTERVAL = 90

# optional: provide specific filter
f = 'userName:cn:@octsim.com'

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

# iterate through user list, check if expired (never logged in, last login > interval - default 90 days)
for user in user_list:
        if "lastLoginSuccessAt" in user:
            last_login = user["lastLoginSuccessAt"]
            now = datetime.utcnow()
            last_login = datetime.strptime(last_login[:10])
            delta = now - last_login
            if delta.days >= INTERVAL:
                user["expired"] = True
            else:
                user["expired"] = False
        else:
            user["expired"] = True


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

expired_room_list = []

for room in room_list:
    for user in user_list:
        if room["name"] == f'{user["id"]}_{user["firstName"]}_{user["lastName"]}' and user["expired"] == True:
            expired_room_list.append(room["id"])

print(f'Expired rooms: {len(expired_room_list)}')


r = nodes.delete_nodes(expired_room_list)

try:
    delete_response = my_dracoon.delete(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if delete_response.status_code == 204:
    print('Delete successful: ' + str(login_response.status_code))
else:
    print(delete_response.status_code)
    print(delete_response.text)


for user in user_list:
    if user["expired"] == True:

        r = users.delete_user(userID=user["id"])
        try:
            delete_user_response = my_dracoon.delete(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)
        
        if delete_user_response.status_code == 204:
            print(f'Delete successful: user id {user["id"]} deleted.')
            print(f'User details: {user["firstName"]} {user["lastName"]} | {user["userName"]}')
            print(str(login_response.status_code))
        else:
            print(f'Delete failed: user id {user["id"]} not deleted.')
            print(f'User details: {user["firstName"]} {user["lastName"]} | {user["userName"]}')
            print(delete_user_response.status_code)
            print(delete_user_response.text)

        





    



