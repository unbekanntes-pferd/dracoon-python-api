# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# List all contents in DRACOON parent folder to CSV
# Requires dracoon package
# Author: Quirin Wierer, 06.10.21
# ---------------------------------------------------------------------------#

from dracoon import core, nodes

import sys
import getpass
import csv

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'dracoon_legacy_scripting'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
#'clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

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

# create dataframe of rooms
# get parentID (0 for root node)
parentID = input('ParentNodeID: ')

r = nodes.search_nodes('*', parentID=parentID, depthLevel=-1, offset=0)
try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if room_response.status_code == 200:
     room_list = []
     total_nodes = room_response.json()["range"]["total"]
     for room in room_response.json()['items']:
            room_list.append(room)
     print(f'Node count: {total_nodes}')
     if total_nodes > 500:
            for offset in range(500, total_nodes, 500):
                r = nodes.search_nodes('*', parentID=parentID, depthLevel=-1, offset=offset)
                try:
                    room_response = my_dracoon.get(r)
                except core.requests.exceptions.RequestException as e:
                    raise SystemExit(e)
                for room in room_response.json()['items']:
                    room_list.append(room)
else:
    e = f'Error getting rooms - details: {room_response.text}'
    raise SystemExit(e)

#create and save list as .csv
# set filename
fileName = f'node_{parentID}_contents.csv'

# create CSV in current directory, write header, iterate through results
with open(fileName, 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['id', 'type', 'name', 'parentPath', 'createdAt (Upload-Datum)', 'createdBy', 'updatedAt (Interne Modifikation)', 'updatedby'])

    for room in room_list:

        roomID = room["id"]
        roomtype = room["type"]
        roomname = room["name"]
        roomparentPath = room["parentPath"]
        roomcreatedAt = room["createdAt"]
        if "createdBy" in room: roomcreatedBy = room["createdBy"]['userName']
        roomupdatedAt = room["updatedAt"]
        if "updatedBy" in room: roomupdatedBy = room["updatedBy"]['userName']

        csv_writer.writerow([roomID, roomtype, roomname, roomparentPath,
                            roomcreatedAt, roomcreatedBy, roomupdatedAt, roomupdatedBy])

print(f'CSV room report (room id: {roomID}) created: ' + fileName)
