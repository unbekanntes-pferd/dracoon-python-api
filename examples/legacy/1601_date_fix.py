# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Perform bulk edit on file meta data (fix 1601 wrong date)
# Example updates list of affected files 
# Requires dracoon package
# Author: Octavio Simone, 30.11.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes

import sys
import getpass

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

FILES = [
    {
        "file": "mandant_basisinfo.xlsx",
        "date_modification": "2021-06-04T09:00:00.000Z",
        "date_creation": "2021-05-27T09:00:00.000Z"
    },
    {
        "file": "_liesmich.txt",
        "date_modification": "2021-02-09T09:00:00.000Z",
        "date_creation": "2021-02-09T09:00:00.000Z"
    }
]
parent_id = 444 #insert parent id

for _file in FILES:

    # create filter for files based on file name
    f = f'type:eq:file'

    # create request to get search for all files with expiration date greater than November 29th 2020
    r = nodes.search_nodes(search=_file["file"], parentID=parent_id, depthLevel=-1, offset=0, filter=f)

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
        # get total amount of files
        total_files = file_response.json()['range']['total']
    else:
        print('Error getting file list.')
        print(file_response.status_code)
        print(file_response.text)
        sys.exit()

    # in case files exceed 500 items, get reamining rooms via offset
    if total_files > 500:
        for offset in range(500, total_files, 500):
            r = nodes.search_nodes(
                search=file["file"], parentID=parent_id, depthLevel=-1, offset=offset, filter=f)
            file_response = my_dracoon.get(r)
            for file in file_response.json()['items']:
                file_list.append(file)

    print(f"{len(file_list)} files of name '{_file['file']}'' to process.")

    # generate request body - set expiration to False
    for item in file_list:
        
        # only update if wrong timestamp provided
        if item["timestampModification"] == '1601-01-01T00:00:00.000Z':
            params = {
            "timestampCreation": _file["date_creation"],
            "timestampModification": _file["date_modification"]
            }

            # create request to update files
            r = nodes.update_file(nodeID=file["id"], params=params)

            config_response = my_dracoon.put(r)
            if config_response.status_code == 200:
                print(f'Successfully updated timestamps for file {item["parentPath"]}{item["name"]}')
            else:
                print(f'Error updating file {item["name"]}')
                print(f'Error in room {item["parentPath"]}')
                print(f'Details: {config_response.text}')
                print(f'Status: {config_response.status_code}')
                continue
        # continue with next item
        else:
            continue

