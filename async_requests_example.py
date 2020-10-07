# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Export user list to CSV file
# Requires dracoon package
# Author: Octavio Simone, 04.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, users, nodes
import sys
import getpass
import csv
import os
import aiohttp
import asyncio

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'dracoon_legacy_scripting'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo-os.dracoon.com'  # replace with own DRACOON url

# create DRACOON object
my_dracoon = core.Dracoon(clientID)
my_dracoon.set_URLs(baseURL)

# get user login credentials (basic, AD possible)
RO_user = input('Username: ')
RO_password = getpass.getpass('Password: ')


# perform request with authenticated DRACOON instance
async def main():


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

# optional: provide specific filter
    f = 'email:cn:dracoon.com'


# create list for users
    user_list = []

# generate request to get users - filter can be omitted, default is no filter
    r = users.get_users(offset=0, filter=f)

# generate request to get nodes - filter can be omitted, default is no filter
    r2 = nodes.get_nodes(roomManager='false', parentID=0,
                     offset=0, filter='type:eq:room')
    try:
         async with aiohttp.ClientSession() as session:
             user_response = await my_dracoon.async_get(r, session)
             room_response = await my_dracoon.async_get(r2, session)

             # to be replaced with async CSV output function
             print(user_response)
             print(room_response)

    except aiohttp.ClientConnectionError as e:
        raise SystemExit(e)


loop = asyncio.get_event_loop()
loop.run_until_complete(main())
