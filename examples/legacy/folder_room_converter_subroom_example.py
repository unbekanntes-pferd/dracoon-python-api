# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Convert folders into rooms with inherited permissions
# Example first renames all folders, then creates rooms and moves files
# from folders to rooms and creates a sub room
# Requires dracoon package
# Author: Octavio Simone, 02.07.2021
# ---------------------------------------------------------------------------#

from dracoon import core, nodes

import sys
import getpass

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# create object to authenticate and send requests - client secret is optional (e.g. for use with dracoon_legacy_scripting)
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

# provide a list (or single id for parent)
parent_list = [999]

for parentID in parent_list: 
    # create request to get search for all folders in a parent room
    r = nodes.search_nodes('*', parentID=parentID, depthLevel=0, offset=0, filter='type:eq:folder')

    try:
        folder_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    folder_list = []
    room_list = []

    if folder_response.status_code == 200:
        folder_list = folder_response.json()["items"]
    else:
        e = f'Error getting folders - details: {folder_response.text}'
        raise SystemExit(e)


    # rename all folder with trailing "_"
    for folder in folder_list:
        rename_params = {
            "name": folder["name"] + "_"
        }

        r = nodes.update_folder(folder["id"], rename_params)
        try:
            rename_response = my_dracoon.put(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)
        if rename_response == 200:
            print(f'Folder {folder["name"]} renamed to {folder["name"]}_')
        else:
            print(f'Cannot rename folder {folder["name"]}.')
            print(f'Details: {rename_response.text}')
            continue


    # iterate through all folders in parent ID, create room and move files
    for folder in folder_list:

        first_name = folder["name"].split(" ")[0]
        last_name = folder["name"].split(" ")[1]
        user_email = first_name[0] + "." + last_name + "@dracoon.com"

        f = f'user:cn:{user_email}|isGranted:eq:any'

        r = nodes.get_room_users(nodeID=parentID, filter=f)

        try:
            user_info_response = my_dracoon.get(r)
        except core.requests.exceptions.RequestException as e:
            print(f'Could not get user info for {first_name + " " + last_name}: Connection error')
            continue
        
        if user_info_response.status_code == 200 and len(user_info_response.json()["items"]) > 0:
            user_id = user_info_response.json()["items"][0]
            print(f'User id for user with mail {user_email} is {user_id}')

        params = {
            "name": folder["name"],
            "parentId": folder["parentId"],
            "inheritPermissions": True
        }

        # create request for room creation with name and parent path
        # try to create a room
        r = nodes.create_room(params)
        try:
            room_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        room_created = False

        # respond to creation request
        if room_response.status_code == 201:
            room_id = room_response.json()["id"]
            room_list.append(room_id)
            print(f'Room for {folder["name"]} created.')
            room_created = True
        else:
            print('Room not created.')
            print(f'Details: {room_response.text}')
            continue

        if room_created == True:

            params = {
            "name": 'Share',
            "parentId": room_id,
            "inheritPermissions": False,
            "adminIds": [1, 2]
        }
            r = nodes.create_room(params)
            try:
                room_response = my_dracoon.post(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)

            

        # create a request to get all files and folders in a folder
        r = nodes.search_nodes(
            '*', parentID=folder["id"], depthLevel=0, offset=0, filter='type:eq:folder:file')

    # send request for files in folder
        try:
            file_response = my_dracoon.get(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        file_list = []

        # check if request successful - if not, continue to next folder
        if file_response.status_code == 200:
            file_list = file_response.json()["items"]
        else:
            print('Files could not be obtained.')
            print(f'Details: {file_response.text}')
            continue

        # check if files need to be copied - if no files, go to next folder
        if file_list == []:
            print(f'No files to move in folder {folder["name"]}.')
            continue

        # create a list of files to move them with name and id
        file_list_prepared = []

        for file in file_list:
            file_obj = {
                "id": file["id"],
                "name": file["name"]
            }
            file_list_prepared.append(file_obj)

        # create request to move all files from folder to room

        move_params = {
            "items": file_list_prepared,
            "resolutionStrategy": "autorename",
            "keepShareLinks": False
        }

        r = nodes.move_nodes(room_id, move_params)

        # send request to move files
        try:
            move_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        # check if files were moved or report back error
        if move_response.status_code == 200:
            print(f'Moved {len(file_list)} nodes to room {folder["name"]}')
        else:
            print(f'Could not move files/folders. Error details: {move_response.text}')
