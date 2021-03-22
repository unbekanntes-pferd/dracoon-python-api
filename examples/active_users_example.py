# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export room log to CSV file
# Requires dracoon package
# Author: Octavio Simone, 30.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, eventlog
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

date_start = '2021-01-01T00:00:00'
date_end = '2021-02-01T00:00:00'


# generate request to get events
r = eventlog.get_events(dateStart=date_start, dateEnd=date_end)

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
            r = eventlog.get_events(dateStart=date_start,dateEnd=date_end, operationID=None, userID=None, offset=offset)
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
fileName = 'active_users.csv'

# create list to hold users 
user_list = []

# get all user names 
for event in event_list:
    user_list.append(event["userName"])

# get only unique users
user_list = set(user_list)

last_user_events = []



# get last event for all users
for user in user_list:
    for event in event_list:
        # get first event 
        if user == event["userName"]:
            event_obj = {
                "userName": user,
                "event": event["operationName"],
                "time": event["time"],
            }
            last_user_events.append(event_obj)
            break



# create CSV in current directory, write header, iterate through results
with open(fileName, 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['userName', 'event', 'time' ])

    for event in last_user_events:

        csv_writer.writerow([event["userName"], event["event"], event["time"]])

print(
    f'CSV report of last active users from {date_start} to {date_end} saved in ' + os.getcwd() + '/' + fileName)
