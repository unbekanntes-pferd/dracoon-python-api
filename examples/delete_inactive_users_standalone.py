# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Delete inactive users as standalone if home room is empty
# Requires dracoon package
# Author: Octavio Simone, 28.04.2021
# ---------------------------------------------------------------------------#

from typing import List
from dracoon import core, users, eventlog
import sys
import csv
import getpass
import argparse


# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# create DRACOON object
my_dracoon = core.Dracoon(clientID)
my_dracoon.set_URLs(baseURL)

# get user login credentials (basic, AD possible)
RO_user = input('Username: ')
RO_password = getpass.getpass('Password: ')
HOMEROOM_PARENT_ID = 4
LTS = False
LOGIN = "userName"

if LTS:
    LOGIN = "login"

def authenticate(user: str, password: str):
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
        sys.exit(2)  # exit script if login not successful

# parse a csv file into a list of user ids
def parse_user_csv(csv_file) -> List[int]:

    user_list = []

    # open CSV file (example: import.csv in cwd)
    with open(csv_file, 'r') as f:
        csv_reader = csv.reader(f, delimiter=",")
        # skip header
        next(csv_reader)

        # csv format: 'id', 'firstName', 'lastName', 'email'
        for user in csv_reader:
            user_id = int(user[0])
            user_list.append(user_id)

        return user_list

# get user info based on id
def get_user_info(user_id: int):

    r = users.get_user(userID=user_id)
    try:
        get_user_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return get_user_response.json()

# delete users
def delete_users(user_list: List[int], parent_id: int, mode: str):

    for user in user_list:
        if mode == "safe":
            room_empty = check_home_room_empty(user, parent_id)
            if room_empty == False:
                print(f"User with id {user} has a non-empty home room.")
                user_info = get_user_info(user)
                print(f"User details: User {user_info[LOGIN]} – Name: {user_info['firstName']} {user_info['lastName']}")
                continue
            elif room_empty == None:
                print(f"User with id {user} has no home room.")
                user_info = get_user_info(user)
                if LOGIN in user_info:
                   print(f"User details: User {user_info[LOGIN]} – Name: {user_info['firstName']} {user_info['lastName']}")
                continue

        r = users.delete_user(userID=user)
        try:
            delete_user_response = my_dracoon.delete(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)
            
        if delete_user_response.status_code == 204:
            print(f'Delete successful: user id {user} deleted.')
            print(str(delete_user_response.status_code))
        else:
            print(f'Delete failed: user id {user} not deleted.')
            if delete_user_response.status_code != 404:
               user_info = get_user_info(user)
               print(f"User details: User {user_info[LOGIN]} – Name: {user_info['firstName']} {user_info['lastName']}")
            if delete_user_response.status_code == 400:
                last_admin_rooms = get_last_admin_rooms(user)

                if "items" in last_admin_rooms:
                    for room in last_admin_rooms["items"]:
                        print(f"User is last admin in room with id {room['id']} – {room['parentPath']}/{room['name']}")

            print(delete_user_response.status_code)
            print(delete_user_response.text)

# check if a room is empty
def check_home_room_empty(user_id: int, parent_id: int) -> bool:
    r = eventlog.get_user_permissions(filter=f'nodeParentId:eq:{parent_id}')

    try:
        homeroom_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if homeroom_response.status_code == 200:
        home_rooms = homeroom_response.json()
    else:
        print("Error getting home rooms / permissions")
        print(homeroom_response.status_code)
        print(homeroom_response.text)
        return None

    for room in home_rooms:
        user_permissions = room["auditUserPermissionList"]
        for user in user_permissions:
            if user["userId"] == user_id:
                room_id, node_size = room["nodeId"], room["nodeSize"]

                if node_size > 0:
                    return False
                else:
                    return True

def get_last_admin_rooms(user_id: int):
    r = users.get_user_last_admin_rooms(userID=user_id)

    try:
        get_room_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    return get_room_response.json()


# main script 
def main(csv_file, mode):
    # authenticate
    authenticate(RO_user, RO_password)
    
    # parse user csv list
    user_list = parse_user_csv(csv_file)

    # delete users 
    delete_users(user_list, HOMEROOM_PARENT_ID, mode)

# parse CLI arguments 
def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="CSV file to parse – must contain user ids in first column.")
    ap.add_argument("-m", "--mode", required=False, help="Mode: 'safe' to check home room content, 'force' to delete all with no check.")
    args = vars(ap.parse_args())

    # if no file is given, exit
    if args["file"] is None:
        print("Providing a csv file is mandatory.")
        sys.exit(2)
    else:
        csv_file = args["file"]

    # default value for mode is safe (check home rooms)
    if args["mode"] is None:
        mode = "safe"
    elif args["mode"] != "force":
        print("Only modes safe and force allowed.")
        sys.exit(2)
    else:
        mode = args["mode"]
    
    return csv_file, mode 


# only runs if script is executed as standalone 
if __name__ == "__main__":
    #parse command line arguments
    csv_file, mode = parse_arguments()
    print(f"Using csv file {csv_file}")
    print(f"Using {mode} mode")

    # execute main script
    main(csv_file, mode)


        





    



