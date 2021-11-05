from dracoon import core, users, nodes, groups
import sys
import getpass
import csv
import argparse

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'dracoon_legacy_scripting'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo-os.dracoon.com'  # replace with own DRACOON url

# create DRACOON object
my_dracoon = core.Dracoon(clientID)
my_dracoon.set_URLs(baseURL)

ADMIN_ID = 60
PARENT_ID = 8325
GROUP_NAMES = ["Extern", "Management", "Lesen", "Bearbeiten"]

# log in to DRACOON
def log_in(RO_user: str, RO_password: str):
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

# create or get group with given name
def create_or_get_group(name: str) -> int:

        params = {
           "name": name
       }

        group_id = 0

        # create and send rquest
        r = groups.create_group(params)
        try:
            create_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if create_response.status_code == 201:
            print(f"Group {name} created.")
            group_id = create_response.json()["id"]
        elif create_response.status_code == 409:
            print(f"Group {name} already exists: {create_response.status_code}")
            r = groups.get_groups(filter=f"name:cn:{name}")
            try:
                get_group_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            if get_group_response.status_code == 200:
                if len(get_group_response.json()["items"]) > 0:
                    group_id = get_group_response.json()["items"][0]["id"]
                    print(f"Group {name} found.")
                else:
                    print(f"Group {name} not found.")

        return group_id

# get list of companies from CSV        
def parse_csv(file_path: str): 

    companies = []

    # open CSV file (example: import.csv in cwd)
    with open(file_path, 'r') as f:
        csv_reader = csv.reader(f, delimiter=";")
        # skip header
        next(csv_reader)

        # csv format: 'comapny', 'manager'
        for company in csv_reader:
            company_name = company[0]
            company_manager = company[1]
            companies.append({"name": company_name, "manager": company_manager})
 
        return companies 

def get_user_id(username: str) -> int:
    
    user_id = 0

    r = users.get_users(filter=f"userName:eq:{username}")
    try:
        get_user_response = my_dracoon.get(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)
    if get_user_response.status_code == 200:
        if len(get_user_response.json()["items"]) > 0:
            user_id = get_user_response.json()["items"][0]["id"]
            print(f"User {username} found.")
        else:
            print(f"User {username} not found.")
    return user_id


def create_room(company: dict, manager_id: int, manager_group_id: int) -> int:

        room_id = 0

        params = {
            "name": company["name"],
            "adminIds": [manager_id, ADMIN_ID],
            "adminGroupIds": [manager_group_id],
            "parentId": PARENT_ID,
            "inheritPermissions": False
        }
        r = nodes.create_room(params=params)

        try:
            room_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if room_response.status_code == 201:
            print(f"Room for {company['name']} (Manager: {company['manager']}) created.")
            room_id = room_response.json()["id"]
        elif room_response.status_code >= 400 and room_response.status_code < 500:
            print(f"Room for {company['name']} (Manager: {company['manager']}) could not be created - error: {room_response.status_code}")
            print(room_response.json()["message"])
            print(room_response.json()["debugInfo"])
        else:
            print(f"Room for {company['name']} (Manager: {company['manager']}) could not be created - error: {room_response.status_code}")
        
        return room_id


def copy_template(room_id: int):

        params = {
            "items":[
                {
                "id": 8327,
                "name": "Finanzbuchhaltung"
            }, 
            {
                "id": 8328,
                "name": "Eingang"
            },
             {
                "id": 8329,
                "name": "Ausgang"
            },
             {
                "id": 8330,
                "name": "Dokumente"
            }
            ]
        } 

        r = nodes.copy_nodes(room_id, params)

        try:
            copy_response = my_dracoon.post(r)
        except core.requests.exceptions.RequestException as e:
            raise SystemExit(e)

        if copy_response.status_code == 201:
            print(f"Templates for room created.")
        elif copy_response.status_code >= 400 and copy_response.status_code < 500:
            print(f"Templates for room could not be created - error: {copy_response.status_code}")
            print(copy_response.json()["message"])
            print(copy_response.json()["debugInfo"])

        else:
            print(f"Templates for room could not be created - error: {copy_response.status_code}")
 

def remove_admin_right(room_id: int):

    params = {
            "items": [
    {
      "id": ADMIN_ID,
      "permissions": {
        "manage": False,
        "read": False,
        "create": False,
        "change": False,
        "delete": False,
        "manageDownloadShare": False,
        "manageUploadShare": False,
        "readRecycleBin": False,
        "restoreRecycleBin": False,
        "deleteRecycleBin": False
      }
    }
  ]
        }

    r = nodes.update_room_users(nodeID=room_id, params=params)

    try:
        unassign_response = my_dracoon.put(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if unassign_response.status_code == 204:
        print(f"Removed admin rights for room.")
    elif unassign_response.status_code >= 400 and unassign_response.status_code < 500:
        print(f"Removing admin rights for room failed - error: {unassign_response.status_code}")
        print(unassign_response.json()["message"])
        print(unassign_response.json()["debugInfo"])
    else:
        print(f"Removed admin rights for room of user failed - error: {unassign_response.status_code}")


def assign_user_to_group(user_id: int, group_id: int):

    r = groups.update_group_users([user_id], group_id)

    try:
        group_response = my_dracoon.post(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if group_response.status_code == 200:
        print(f"Added user to corresponding group.")
    elif group_response.status_code >= 400 and group_response.status_code < 500:
        print(f"Adding user to group failed - error: {group_response.status_code}")
        print(group_response.json()["message"])
        print(group_response.json()["debugInfo"])
    else:
        print(f"Adding user to group failed - error: {group_response.status_code}")

# parse CLI arguments 
def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="CSV file to parse – must contain user ids in first column.")
    args = vars(ap.parse_args())

    # if no file is given, exit
    if args["file"] is None:
        print("Providing a csv file is mandatory.")
        sys.exit(2)
    else:
        csv_file = args["file"]
    
    return csv_file


def main():
    csv_file = parse_arguments()
    print(f"Using csv file {csv_file}")
    # get user login credentials (basic, AD possible)
    RO_user = input('Username: ')
    RO_password = getpass.getpass('Password: ')

    log_in(RO_user=RO_user, RO_password=RO_password)
    
    company_list = parse_csv(csv_file)

    for company in company_list:

        for group_type in GROUP_NAMES:
            group_name = company["name"] + "_" + group_type
            group_id = create_or_get_group(group_name)
            if group_name == company["name"] + "_" + "Management":
                management_group_id = group_id
                manager_id = get_user_id(username=company["manager"])
                assign_user_to_group(user_id=manager_id, group_id=management_group_id)
          
        room_id = create_room(company=company, manager_id=manager_id, manager_group_id=management_group_id)

        if room_id > 0:
            copy_template(room_id=room_id)
            remove_admin_right(room_id=room_id)

    parse_csv()


if __name__ == "__main__":
    main()