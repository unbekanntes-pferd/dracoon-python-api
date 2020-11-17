# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Perform bulk edit on data rooms one can manage
# Example first renames all folders, then creates rooms and moves files
# from folders to rooms
# into a target room as CSV
# Requires dracoon package
# Author: Octavio Simone, 04.11.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes

import sys
import getpass

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'dracoon_legacy_scripting'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo-os.dracoon.com'  # replace with own DRACOON url

# create object to authenticate and send requests - client secret is optional (e.g. for use with dracoon_legacy_scripting)
my_dracoon = core.Dracoon(clientID)
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

# create request to get search for all folders in a parent room
r = nodes.search_nodes('*', parentID=0, depthLevel=-1, offset=0, filter='type:eq:room')

# perform request with authenticated DRACOON instance
try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:  
    raise SystemExit(e)

room_list = []

# if call successful, check populate list
if room_response.status_code == 200:

    # add rooms to list if manage permissions are available
   for room in room_response.json()['items']:
       if room["permissions"]["manage"] == True:
           room_list.append(room)

#get total amount of rooms
total_rooms = room_response.json()['range']['total']

#in case rooms exceed 500 items, get reamining rooms via offset
if total_rooms > 500:
    for offset in range(500, total_rooms, 500):
        r = nodes.search_nodes('*', parentID=0, depthLevel=-1, offset=offset, filter='type:eq:room')
        room_response = my_dracoon.get(r)
        for room in room_response.json()['items']:
            if room["permissions"]["manage"] == True:
                room_list.append(room)

print(f"{len(room_list)} rooms to process.")

# set default retention period to 30 days for each room 
for room in room_list: 
    params = {
        "recycleBinRetentionPeriod": 30,
    }

    r = nodes.config_room(nodeID=room["id"], params=params)

    config_response = my_dracoon.put(r)
    if config_response.status_code == 200:
        print(f'Successfully set recycle bin retention period to 30 days for room {room["name"]}')
    else: 
        print(f'Error setting recycle bin retention period for room {room["name"]}')
        print(f'Details: {config_response.text}')
        print(f'Status: {config_response.status_code}')
        continue

    




