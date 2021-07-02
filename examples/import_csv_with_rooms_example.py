# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Import user list from CSV file, create room
# Requires dracoon package
# Author: Octavio Simone, 02.07.2021
# ---------------------------------------------------------------------------#

from dracoon import core, users, nodes
import sys
import getpass
import csv
import os

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# create DRACOON object
my_dracoon = core.Dracoon(clientID, clientSecret)
my_dracoon.set_URLs(baseURL)

# get user login credentials (basic, AD possible)
RO_user = input('Username: ')
RO_password = getpass.getpass('Password: ')
PARENT_ID = 999

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


# open CSV file (example: import.csv in cwd)
with open('csv_import.csv', 'r') as f:
    csv_reader = csv.reader(f, delimiter=";")
    # skip header
    next(csv_reader)

    # csv format: 'firstName', 'lastName', 'email'
    for user in csv_reader:
        firstName = user[0]
        lastName = user[1]
        email = user[2]
        room_name = email.split("@")[0]
        
        # for data model please refer to API documentation - this model is compatible with current DRACOON Cloud release
        # for DRACOON Server model see https://demo.dracoon.com/api/swagger-ui.html
        params = {
            "firstName": firstName,
            "lastName": lastName,
            "userName": email,
            "receiverLanguage": "de-DE",
            "email": email,
            "notifyUser": False,
            "authData": {
                "method": "active_directory",
                "username": email,
                "ad_config_id": 1,
                "mustChangePassword": False,
            },
            "isNonmemberViewer": True
        }

        created_success = False 
        
        # create and send rquest
        r = users.create_user(params)
        try:
            create_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if create_response.status_code == 201:
            created_success = True
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) created.")
            user_id = create_response.json()["id"]
        elif create_response.status_code >= 400 and create_response.status_code < 500:
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) could not be created - error: {create_response.status_code}")
            print(create_response.json()["message"])
            print(create_response.json()["debugInfo"])
        else:
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) could not be created - error: {create_response.status_code}")


        if created_success == True:

        # try to create a room
            params = {
            "name": room_name,
            "adminIds": [user_id],
            "parentId": PARENT_ID,
            "inheritPermissions": False
        }



            r = nodes.create_room(params)
            try:
                room_response = my_dracoon.post(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)

            # respond to creation request
            if room_response.status_code == 201:
                room_id = room_response.json()["id"]
                print(
                    f'Room {room_name} created.')
            else:
                print(f'Room for {user["userName"]} not created.')
                print(f'Details: {room_response.text}')
      




