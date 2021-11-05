# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Get all 0KB files for rooms one can access
# Stores list as CSV
# Requires dracoon package
# Author: Octavio Simone, 17.12.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes

import sys
import getpass
import csv
import os

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# create object to authenticate and send requests - client secret is optional (e.g. for use with dracoon_legacy_scripting)
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

# create request to get search for all files with expiration date greater than November 29th 2020
r = nodes.search_nodes('*', parentID=0, depthLevel=-1, offset=0, filter='type:eq:file|size:le:1')

# perform request with authenticated DRACOON instance
try:
    file_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:  
    raise SystemExit(e)

file_list = []

# if call successful, check populate list
if file_response.status_code == 200:

    # add files to list 
   for file in file_response.json()['items']:
        file_list.append(file)

#get total amount of files
total_files = file_response.json()['range']['total']

#in case files exceed 500 items, get reamining rooms via offset
if total_files > 500:
    for offset in range(500, total_files, 500):
        r = nodes.search_nodes('*', parentID=0, depthLevel=-1, offset=0, filter='type:eq:file|size:le:1')
        file_response = my_dracoon.get(r)
        for file in file_response.json()['items']:
            file_list.append(file)

print(f"{len(file_list)} files to process.")


with open('0KB_list.csv', 'w', encoding='utf-8', newline='') as f:
    csv_writer = csv.writer(f, delimiter=',')
    csv_writer.writerow(['id', 'name', 'path', 'filetype', 'size', 'createdAt',   'updatedAt','updatedByEmail', 'updatedByUserName'])

    for file in file_list:

        # check for roles, expiration and last login
        if "updatedBy" in file:
            updatedEmail = file["updatedBy"]["email"]
            updatedUserName = file["updatedBy"]["userName"]
            updatedAt = file["updatedAt"]
        else: 
            updatedEmail = 'None'
            updatedUserName = 'None'
            updatedAt = 'None'

  
        # write row for current user
        csv_writer.writerow([file["id"], file["name"], file["parentPath"], file["fileType"], file["size"], file["createdAt"], updatedAt, updatedEmail,
                             updatedUserName])


print('CSV user report created:' + os.getcwd() + '/0KB_list.csv')
    






