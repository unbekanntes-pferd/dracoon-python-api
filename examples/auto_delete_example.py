# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Example checks for files older than 90 days and deletes them (based on
# upload into DRACOON (!))
# Requires dracoon package
# Author: Octavio Simone, 21.05.2021
# ---------------------------------------------------------------------------#

from dracoon import core, nodes
import sys
import getpass
from datetime import datetime

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo.dracoon.com'  # replace with own DRACOON url


# target node id of room or folder to download from
targetID = 8888
INTERVAL = 90 # 90 days

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

# create empty file lists (file list for all files, expired files for all expired files)

file_list = []
expired_files = []

# filter for files created for given time interval
f = 'type:eq:file'

# build request to get nodes
r = nodes.search_nodes(parentID=targetID, filter=f, search='*', depthLevel=-1)

# send request
file_response = my_dracoon.get(r)

if file_response.status_code != 200:
    print(f'Error getting file list: {file_response.status_code}')
    print(file_response.text)
    sys.exit()
elif file_response.status_code == 200:
    for file in file_response.json()['items']:
        file_list.append(file)

#get total amount of files
total_files = file_response.json()['range']['total']

#in case files exceed 500 items, get reamining rooms via offset
if total_files > 500:
    for offset in range(500, total_files, 500):
        r = nodes.get_nodes(parentID=targetID, filter=f, offset=offset)
        file_response = my_dracoon.get(r)
        for file in file_response.json()['items']:
            file_list.append(file)



# iterate through list and download only files within given timeframe (example: 900 seconds = 15 minutes interval)
for file in file_list:
    # get datetime string up to seconds
    created_at = file["createdAt"][:19]
    created_at = datetime.strptime(created_at, '%Y-%m-%dT%H:%M:%S')

    # get current datetime
    now = datetime.utcnow()

    # check if file uploaded within given interval (default 15 minutes)
    delta = now - created_at

    if delta.days >= 90:
        print(f'File {file["name"]} expired and will be deleted.')
        expired_files.append(file["id"])


# generate delete request
r = nodes.delete_nodes(expired_files)
try:
    delete_response = my_dracoon.delete(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

# check if successful
if delete_response.status_code == 204:
    print(f'Files moved to recycle bin.')
    r = nodes.empty_recyclebin(nodeIDs=expired_files)
    recyclebin_response = my_dracoon.delete(r)
    if recyclebin_response.status_code == 204:
        print(f'Files removed from recycle bin.')
    else: 
        print('Error emptying recycle bin.')
        print(recyclebin_response.status_code)
        print(recyclebin_response.text)
else:
    print('Error deleting files.')
    print(delete_response.status_code)
    print(delete_response.text)




        

        

        














       
 

        



    

        
    
    
