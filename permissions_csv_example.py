# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export room permissions list to CSV file
# Requires dracoon package 
# Author: Octavio Simone, 23.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, users, eventlog
import sys
import getpass
import csv
import os 

clientID = 'xxxxxx' # replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientSecret = 'xxxxxxx' # replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter 
baseURL = 'https://dracoon.team' # replace with own DRACOON url

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
    sys.exit() # exit script if login not successful 


# create list for rooms 
room_list = []

# generate request to get rooms - filter can be omitted, default is no filter
r = eventlog.get_user_permissions(offset=0)

# perform request with authenticated DRACOON instance
try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:  
    raise SystemExit(e)

# if call successful, check populate list
if room_response.status_code == 200: 
    total_rooms = len(room_response.json())
    for room in room_response.json():
        room_list.append(room)
    print('Added rooms to list.')
    print(f'Room count: {total_rooms}')
    if total_rooms == 500:
        print(f'Please use offset to get remaining rooms.')

else: 
    print(f'Error: {room_response.status_code}')
    print(f'Details: {room_response.text}')

    
# create CSV in current directory, write header, iterate through results
with open('permission_list.csv', 'w', encoding='utf-8', newline = '') as f:
    csv_writer = csv.writer(f, delimiter = ',')
    csv_writer.writerow(['id', 'name', 'parentPath', 'nodeSize', 'encrypted', 'createdAt', 'updatedAt', 
    'userLogin', 'firstName', 'lastName', 'manageRoom', 'read', 'create', 'change', 'delete', 'downloadShares', 'uploadShares', 
    'readRBin', 'restoreRBin', 'deleteRBin'])

    for room in room_list:

        roomId = room["nodeId"]
        roomName = room["nodeName"]
        parentPath = room["nodeParentPath"]
        roomSize = room["nodeSize"]
        isEncrypted = room["nodeIsEncrypted"]
        createdAt = room["nodeCreatedAt"]
        updatedAt = room["nodeUpdatedAt"]
        notAvailable ="n/a"
        print(f"Processing room {roomName}...")

        if len(room["auditUserPermissionList"]) > 0:
            assignedUsers = room["auditUserPermissionList"]
            for user in assignedUsers:  
                userLogin = user["userLogin"]
                firstName = user["userFirstName"]
                lastName = user["userLastName"]
                manageRoom = user["permissions"]["manage"]
                readRight = user["permissions"]["read"]
                createRight = user["permissions"]["create"]
                changeRight = user["permissions"]["change"]
                deleteRight = user["permissions"]["delete"]
                downloadShares = user["permissions"]["manageDownloadShare"]
                uploadShares = user["permissions"]["manageUploadShare"]
                readRBin = user["permissions"]["readRecycleBin"]
                restoreRBin = user["permissions"]["restoreRecycleBin"]
                deleteRBin = user["permissions"]["deleteRecycleBin"]
                csv_writer.writerow([roomId, roomName, parentPath, roomSize, isEncrypted, createdAt, updatedAt, userLogin, firstName, lastName, manageRoom, 
                readRight, createRight, changeRight, deleteRight, downloadShares, uploadShares, readRBin, restoreRBin, deleteRBin])
        else: 
            csv_writer.writerow([roomId, roomName, parentPath, roomSize, isEncrypted, createdAt, updatedAt, notAvailable, notAvailable, notAvailable, notAvailable, 
                notAvailable, notAvailable, notAvailable, notAvailable, notAvailable, notAvailable, notAvailable, notAvailable, notAvailable])

        
print('CSV user report created:' + os.getcwd() + '/user_list.csv')

