# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Basic authentication via password flow 
# requires OAuth client authentication
# Requires dracoon package 
# Author: Octavio Simone, 04.10.2020
# ---------------------------------------------------------------------------#

# for OAuth authentication refer to https://support.dracoon.com/hc/de/articles/115003832605

from dracoon import core
import sys
import getpass

clientID = 'xxxxx' # replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientSecret = 'xxxxxx' # replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter 
baseURL = 'https://dracoon.team' # replace with own DRACOON url

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
    sys.exit() # exit script if login not successful 

