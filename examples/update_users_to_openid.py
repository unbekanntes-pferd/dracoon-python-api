# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Switch LTS users to OpenID 
# Requires dracoon package
# Author: Octavio Simone, 12.05.2021
# ---------------------------------------------------------------------------#

from dracoon import core, users
import getpass


# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://dracoon.team'  # replace with own DRACOON url

# OpenID config ID
oidc_id = 1

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

# filter for specific domain 
f = 'userName:cn:@domain.com'

r = users.get_users(offset=0, filter=f)
user_list = []

user_response = my_dracoon.get(r)

# if call successful, check if user count exceeds 500 and fill list
if user_response.status_code == 200:
    total_users = user_response.json()["range"]["total"]
    for user in user_response.json()['items']:
        user_list.append(user)
    print('Added users to list.')
    print(f'User count: {total_users}')
    if total_users > 500:
        for offset in range(500, total_users, 500):
            r = users.get_users(offset=offset, filter=f)
            try:
                user_response = my_dracoon.get(r)
            except core.requests.exceptions.RequestException as e:
                raise SystemExit(e)
            for user in user_response.json()['items']:
                user_list.append(user)
else:
    print(f'Error: {user_response.status_code}')
    print(f'Details: {user_response.text}')


for user in user_list:

    # payload for LTS 2019-1 version (4.12)
    params = {

        "authData": {
            "method": "openid",
            "login": user["email"],
            "oidConfigId": oidc_id
        }
    }

    # create and send rquest to update user auth info
    r = users.update_user(user["id"], params)
    try:
        update_response = my_dracoon.put(r)
    except core.requests.exceptions.RequestException as e:
        raise SystemExit(e)

    if update_response.status_code == 200:
        print(f"User with email: {user['email']} updated to OpenID.")
    elif update_response.status_code >= 400 and update_response.status_code < 500:
        print(
            f"User with email: {user['email']} could not be updated - error: {update_response.status_code}")
        print(update_response.json()["message"])
        print(update_response.json()["debugInfo"])
    else:
        print(
            f"User with email: {user['email']} could not be updated - error: {update_response.status_code}")
