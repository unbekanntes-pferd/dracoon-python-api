# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Upload files (synchronous)
# Example generates room logs for all root lovel rooms and uploads them
# into a target room as CSV
# Requires dracoon package
# Author: Octavio Simone, 30.10.2020
# ---------------------------------------------------------------------------#

from dracoon import core, nodes, uploads, shares
import sys
import getpass
import csv
import os

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxxxx'
baseURL = 'https://demo.dracoon.com'  # replace with own DRACOON url

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

# file name to upload (if not in cwd, specify path)
fileName = 'test.txt'

# target node id of room or folder to upload to
targetID = 651241

# initiate node id as null value, will be obtained on finalizing upload
node_id = None


_file = open(fileName, 'rb')


upload_file = {
    'file': _file
    }

    # obtain file size for upload
fileSize = os.stat(fileName).st_size

# generate upload channel request
params = {
    "parentId": targetID,
    "name": fileName,
    "size": int(fileSize)
}

r = nodes.create_upload_channel(params)

# get an upload URL 
try:
    upload_channel = my_dracoon.post(r)
except core.requests.exceptions.RequestException as e:
    print('An error ocurred with the upload channel.')
    raise SystemExit(e)

# use upload URL to upload file if upload channel successful 
if upload_channel.status_code == 201: 
    uploadURL = upload_channel.json()["uploadUrl"]
    r = uploads.upload_file(uploadURL, upload_file)
    try:
        upload_response = my_dracoon.post(r)
    except core.requests.exceptions.RequestException as e:
        print('An error ocurred with the file upload.')
        raise SystemExit(e)

# finalize upload or exit on error 
    if upload_response.status_code == 201:
        params = {
            "resolutionStrategy": "autorename",
            "keepShareLinks": False,
            "fileName": fileName
        }
        r = uploads.finalize_upload(uploadURL, params)
        final_upload_response = my_dracoon.put(r)
        node_id = final_upload_response.json()["id"]
        print(f'File uploaded: {final_upload_response.status_code}')
        print(f"Success: {fileName} uploaded to parent ID {targetID}.")
    # error on uploading file
    else: 
        print(f'Error uploading file: {upload_response.status_code}')
        print(f'Details: {upload_response.text}')
# error on getting upload channel 
else: 
    print(f'Error finalizing upload: {upload_channel.status_code}')
    print(f'Details: {upload_channel.text}')

_file.close()

if node_id is None:
    print('File not uploaded – exiting.')
    raise SystemExit()


# create share request 
share_params = {
    "nodeId": node_id,
    "notes": "Some optional public note"
}

r = shares.create_share(share_params)

# send share request 
try: 
    share_response = my_dracoon.post(r)

except core.requests.exceptions.RequestException as e:
    print('An error ocurred during share creation.')
    raise SystemExit(e)

if share_response.status_code == 201:
    share_link = baseURL + '/public/download-shares/' + share_response.json()["accessKey"]
    print(share_link)
else: 
    print(f'Error creating share: {share_response.status_code}')
    print(f'Details: {share_response.text}')