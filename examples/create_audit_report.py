from dracoon import core, reports
from dracoon.reports_models import CreateReport
from pydantic import ValidationError
import sys
import os
import json
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


# get username and password for authentication
def get_credentials():
    # get user login credentials (basic, AD possible)
    RO_user = input('Username: ')
    RO_password = getpass.getpass('Password: ')

    return RO_user, RO_password

# authenticate via basic auth
def authenticate(user: str, password: str):

    # try to authenticate - exit if request fails (timeout, connection error..)
    try:
        login_response = my_dracoon.basic_auth(user, password)
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


# send report creation request 
def create_report(report: CreateReport):
   r = reports.create_report(params=report)

   try:
       report_response = my_dracoon.post(r)
   except core.requests.exceptions.RequestException as e:
       raise SystemExit(e)

   return report_response.json()

# parse JSON file to report model (required for request)
def parse_report(json_file) -> CreateReport:

    # open JSON file, parse to model
    with open(json_file) as file:
        data = json.load(file)
        try: 
           report = CreateReport(data)
        except ValidationError as e:
            print("Invalid report format:")
            print(e.errors())
            sys.exit(2)
        
        return report


# parse CLI arguments 
def parse_arguments():
    ap = argparse.ArgumentParser()
    ap.add_argument("-f", "--file", required=True, help="JSON file to parse – must contain report template.")
    args = vars(ap.parse_args())

    # if no file is given, exit
    if args["file"] is None:
        print("Providing a JSON file is mandatory.")
        sys.exit(2)
    else:
        json_file = args["file"]
    
    # check if JSON file exists
    if os.path.isfile(json_file) != True:
        print(f"Invalid file: {json_file}.")
        print(f"Please provide a valid full path to a JSON file.")
        sys.exit(2)

    return json_file

def main():
    # get CLI arguments
    json_file, target = parse_arguments()
    # get username and password
    user, password = get_credentials()
    # authenticate to DRACOON
    authenticate(user=user, password=password)
    # parse JSON report from file
    report = parse_report(json_file=json_file)
    # create report via API
    create_report(report=report)


if __name__ == "__main__":
    main()