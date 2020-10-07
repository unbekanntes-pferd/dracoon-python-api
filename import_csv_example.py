# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Import user list from CSV file
# Requires dracoon package
# Author: Octavio Simone, 04.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, users
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
with open('import.csv', 'r') as f:
    csv_reader = csv.reader(f)
    # skip header
    next(csv_reader)

    # csv format: 'firstName', 'lastName', 'email'
    for user in csv_reader:
        firstName = user[0]
        lastName = user[1]
        email = user[2]
        
        # for data model please refer to API documentation - this model is compatible with current DRACOON Cloud release
        # for DRACOON Server model see https://demo.dracoon.com/api/swagger-ui.html
        params = {
            "firstName": firstName,
            "lastName": lastName,
            "userName": email,
            "receiverLanguage": "de-DE",
            "email": email,
            "notifyUser": True,
            "authData": {
                "method": "basic",
                "mustChangePassword": True,
            },
            "isNonmemberViewer": True
        }
        
        # create and send rquest
        r = users.create_user(params)
        try:
            create_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if create_response.status_code == 201:
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) created.")
        elif create_response.status_code >= 400 and create_response.status_code < 500:
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) could not be created - error: {create_response.status_code}")
            print(create_response.json()["message"])
            print(create_response.json()["debugInfo"])
        else:
            print(f"User {user[0]} {user[1]} (Email: {user[2]}) could not be created - error: {create_response.status_code}")




