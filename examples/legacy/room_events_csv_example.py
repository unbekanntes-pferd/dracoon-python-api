# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export room log to CSV file
# Requires dracoon package
# Author: Octavio Simone, 30.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes
import getpass
import csv
import os
import sys

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxxxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxxx'
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


# create list for rooms
event_list = []

# get room ID
nodeID = int(input('Room ID: '))

if type(nodeID).__name__ != 'int':
    print('Room ID must be a number.')
    sys.exit()  # exit script if node id is not a number


# generate request to get events
r = nodes.get_events(nodeID)

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
            r = nodes.get_events(nodeID, dateStart="value",dateEnd="value", operationID=None, userID=None, offset=offset)
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
fileName = f'room_{nodeID}_events.csv'


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

print(
    f'CSV room report (room id: {nodeID}) created:' + os.getcwd() + '/' + fileName)
