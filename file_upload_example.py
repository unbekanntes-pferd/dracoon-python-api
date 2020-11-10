# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Upload files (synchronous)
# Example generates room logs for all root lovel rooms and uploads them
# into a target room as CSV
# Requires dracoon package
# Author: Octavio Simone, 30.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes, uploads
import sys
import getpass
import csv
import os

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'dracoon_legacy_scripting'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo-os.dracoon.com'  # replace with own DRACOON url

# create DRACOON object
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

# create list for rooms
event_list = []
room_list = []

# create request to get all top level data rooms (for which a permission exists)
r = nodes.get_nodes(roomManager='false', parentID=0, offset=0, filter='type:eq:room')

try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if room_response.status_code == 200: 
    for room in room_response.json()["items"]:
        room_list.append(room["id"])
else: 
    print('Error getting room ids.')
    sys.exit()

# get a target node id to upload room logs to
targetID = int(input('Enter parent ID for upload: '))


if type(targetID).__name__ != 'int':
    print('Room ID must be a number.')
    sys.exit()  # exit script if node id is not a number


for roomID in room_list: 
    # generate request to get events
    r = nodes.get_events(roomID)
    # perform request with authenticated DRACOON instance
    try:
        event_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)


    # if call successful, check if event count exceeds 500 and fill list
    if event_response.status_code == 200:
        total_events = event_response.json()["range"]["total"]
        for event in event_response.json()['items']:
            event_list.append(event)
        print(f'Event count: {total_events}')
        if total_events > 500:
            for offset in range(500, total_events, 500):
                r = nodes.get_events(roomID, None, None, None, None, offset=offset)
                try:
                    event_response = my_dracoon.get(r)
                except core.requests.exceptions.RequestException as e:
                    raise SystemExit(e)
                for event in event_response.json()['items']:
                    event_list.append(event)
    else:
        print(f'Error: {event_response.status_code}')
        print(f'Details: {event_response.text}')

    # set filename
    fileName = f'room_{roomID}_events.csv'

    # create CSV in current directory, write header, iterate through results
    with open(fileName, 'w', encoding='utf-8', newline='') as f:
        csv_writer = csv.writer(f, delimiter=',')
        csv_writer.writerow(['id', 'time', 'userID', 'userName',
                            'userClient', 'operationName', 'status', 'message', ])

        for event in event_list:

            eventID = event["id"]
            eventTime = event["time"]
            eventUserID = event["userId"]
            eventUserName = event["userName"]
            eventUserClient = event["userClient"] if "userClient" in event else "n/a"
            operationName = event["operationName"]
            status = event["status"]
            message = event["message"]

            csv_writer.writerow([eventID, eventTime, eventUserID, eventUserName,
                                eventUserClient, operationName, status, message])

    print(f'CSV room report (room id: {roomID}) created: ' + fileName)


    #with open(fileName, 'rb') as upload_file:

    _file = open(fileName, 'rb')


    upload_file = {
        'file': _file
        }

        # obtain file size for upload
    fileSize = os.stat(fileName).st_size

    # generate upload channel request
    params = {
        "parentId": targetID,
        "name": fileName,
        "size": int(fileSize)
    }

    r = nodes.create_upload_channel(params)

    # get an upload URL 
    try:
        upload_channel = my_dracoon.post(r)
    except core.requests.exceptions.RequestException as e:
        print('An error ocurred with the upload channel.')
        raise SystemExit(e)

    # use upload URL to upload file if upload channel successful 
    if upload_channel.status_code == 201: 
        uploadURL = upload_channel.json()["uploadUrl"]
        r = uploads.upload_file(uploadURL, upload_file)
        try:
            upload_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            print('An error ocurred with the file upload.')
            raise SystemExit(e)

    # finalize upload or exit on error 
        if upload_response.status_code == 201:
            params = {
                "resolutionStrategy": "autorename",
                "keepShareLinks": False,
                "fileName": fileName
            }
            r = uploads.finalize_upload(uploadURL, params)
            final_upload_response = my_dracoon.put(r)
            print(f'File uploaded: {final_upload_response.status_code}')
            print(f"Success: {fileName} uploaded to parent ID {targetID}.")
        # error on uploading file
        else: 
            print(f'Error uploading file: {upload_response.status_code}')
            print(f'Details: {upload_response.text}')
    # error on getting upload channel 
    else: 
        print(f'Error finalizing upload: {upload_channel.status_code}')
        print(f'Details: {upload_channel.text}')

    _file.close()







