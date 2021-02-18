
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

# get list of rooms

parentID = 59

r = nodes.search_nodes('*', parentID=parentID, depthLevel=-1, offset=0, filter='type:eq:room')
try:
    room_response = my_dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if room_response.status_code == 200:
    parent_list = room_response.json()["items"]
else:
    e = f'Error getting rooms - details: {room_response.text}'
    raise SystemExit(e)

# provide a list (or single id for parent)

room_list = []

for room in parent_list:
   room_list.append(room['id'])


print(room_list)