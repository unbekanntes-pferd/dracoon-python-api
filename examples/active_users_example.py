# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export active and inactive users in given timeframe to CSV file
# Requires dracoon package
# Author: Octavio Simone, 22.03.2021 (updated: 12.08.2021)
# ---------------------------------------------------------------------------#

from dracoon import core, eventlog, users
import csv
import os
import sys
import getpass

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxx'
baseURL = 'https://demo.dracoon.com'  # replace with own DRACOON url

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
event_list = []

date_start = '2021-05-01T00:00:00'
date_end = '2021-08-01T00:00:00'


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
        if "AUTH" in event["operationName"]:
            continue
        else:
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
                if "AUTH" in event["operationName"]:
                    continue
                else:
                    event_list.append(event)
                
else:
    print(f'Error: {event_response.status_code}')
    print(f'Details: {event_response.text}')

# set filename
active_fileName = 'active_users.csv'
inactive_fileName = 'inactive_users.csv'

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


# create list for total users
total_user_list = []

# generate request to get users - filter can be omitted, default is no filter
r = users.get_users(offset=0)
# perform request with authenticated DRACOON instance
try:
    user_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

# if call successful, check if user count exceeds 500 and fill list
if user_response.status_code == 200:
    total_users = user_response.json()["range"]["total"]
    for user in user_response.json()['items']:
        total_user_list.append(user)
    print('Added users to list.')
    print(f'User count: {total_users}')
    if total_users > 500:
        for offset in range(500, total_users, 500):
            r = users.get_users(offset=offset)
            try:
                user_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            for user in user_response.json()['items']:
                total_user_list.append(user)
else:
    print(f'Error: {user_response.status_code}')
    print(f'Details: {user_response.text}')

inactive_user_list = []

for user in total_user_list:
    if user["userName"] in user_list:
        continue

    inactive_user_list.append(user)

# create CSV in current directory, write header, iterate through results
with open(active_fileName, 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['userName', 'event', 'time' ])

    for event in last_user_events:

        csv_writer.writerow([event["userName"], event["event"], event["time"]])

print(
    f'CSV report of last active users from {date_start} to {date_end} saved in ' + os.getcwd() + '/' + active_fileName)


# create CSV in current directory, write header, iterate through results
with open(inactive_fileName, 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['userName', 'email', 'firstName', 'lastName', 'lastLogin' ])

    for user in inactive_user_list:

        lastLogin = None
        
        if "lastLoginSuccessAt" in user:
            lastLogin = user["lastLoginSuccessAt"]
        else:
            lastLogin = "Never logged in."


        csv_writer.writerow([user["userName"], user["email"], user["firstName"], user["lastName"], lastLogin])

print(
    f'CSV report of inactive users from {date_start} to {date_end} saved in ' + os.getcwd() + '/' + inactive_fileName)