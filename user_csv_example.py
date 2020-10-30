# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export user list to CSV file
# Requires dracoon package
# Author: Octavio Simone, 04.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, users
import sys
import getpass
import csv
import os

clientID = 'xxxxxx'  # replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
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

# optional: provide specific filter
f = 'email:cn:dracoon.com'


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


# create CSV in current directory, write header, iterate through results
with open('user_list.csv', 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['id', 'firstName', 'lastName', 'email', 'login', 'createdAt', 'lastLoginSuccessAt', 'isConfigManager', 'isUserManager',
                         'isGroupManager', 'isRoomManager', 'isAuditor', 'isNonMemberViewer', 'expirationDate', 'isLocked'])

    for user in user_list:

        # check for roles, expiration and last login
        if "userRoles" in user:
            for role in user["userRoles"]["items"]:

                isConfigManager = 'True' if role["id"] == 1 else 'False'
                isUserManager = 'True' if role["id"] == 2 else 'False'
                isGroupManager = 'True' if role["id"] == 3 else 'False'
                isRoomManager = 'True' if role["id"] == 4 else 'False'
                isAuditor = 'True' if role["id"] == 5 else 'False'
                isNonMemberViewer = 'True' if role["id"] == 6 else 'False'

        expirationDate = user["expireAt"] if "expireAt" in user else 'None'
        lastLoginSuccessAt = user["lastLoginSuccessAt"] if "lastLoginSuccessAt" in user else 'Never logged in'

        # write row for current user
        csv_writer.writerow([user["id"], user["firstName"], user["lastName"], user["email"], user["login"], user["createdAt"],
                             lastLoginSuccessAt, isConfigManager, isUserManager, isGroupManager, isRoomManager, isAuditor,
                             isNonMemberViewer, expirationDate, user["isLocked"]])


print('CSV user report created:' + os.getcwd() + '/user_list.csv')