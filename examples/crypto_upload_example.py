# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Encrypt a file and upload (with initial missing file keys)
# WARNING: no chunking, this is a simple example
# For large files, encryption and upload should be chunked to avoid 
# trying to load the complete file into memory
# Requires dracoon package
# Author: Octavio Simone, 12.06.2021
# ---------------------------------------------------------------------------#


from dracoon import core, nodes, crypto, user, uploads
import getpass
import os

# base settings

client_id = 'xxxx'
client_secret = 'xxxx'
base_url = 'https://dracoon.team'

# initialize dracoon
dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
dracoon.set_URLs(baseURL=base_url)

# authenticate
print(dracoon.get_code_url())
auth_code = input('Enter auth code:')

dracoon.oauth_code_auth(code=auth_code)

# get user keypair

r = user.get_user_keypair()
print(r)

try:
    keypair_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if keypair_response.status_code == 200:
    enc_keypair = keypair_response.json()
    print(f'Retrieved user keypair')
else:
    print('Could not retrieve keypair')

r = user.get_account_information()

try:
    account_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if account_response.status_code == 200:
    user_id = account_response.json()["id"]
    print(f'Retrieved user account information')
else:
    print('Could not retrieve account information')

# prompt for decryption password
decrypt_password =  getpass.getpass('Enter decryption password:')

# get plain keypair (private key)
plain_keypair = crypto.decrypt_private_key(
    secret=decrypt_password, keypair=enc_keypair)

FILENAME = 'test.txt' # replace with full path and name
TARGET = 999 # replace with parent id for upload

_file = open(FILENAME, 'rb')
plain_data = _file.read()

# check if RSA 2048 or 4096
file_key_version = crypto.get_file_key_version(keypair=enc_keypair)

# generate plain file key
plain_file_key = crypto.create_file_key(version=file_key_version)

# encrypt bytes (AES 256 GCM)
enc_bytes, plain_file_key = crypto.encrypt_bytes(
    plain_data=plain_data, plain_file_key=plain_file_key)

# encrypt file key (with public key of keypair)
enc_file_key = crypto.encrypt_file_key(
    plain_file_key=plain_file_key, keypair=plain_keypair)

_file.close()

upload_file = {
    'file': enc_bytes
}

# obtain file size for upload
filesize = os.stat(FILENAME).st_size

# generate upload channel request
params = {
    "parentId": TARGET,
    "name": FILENAME,
    "size": int(filesize)
}

r = nodes.create_upload_channel(params)

# get an upload URL
try:
    upload_channel = dracoon.post(r)
except core.requests.exceptions.RequestException as e:
    print('An error ocurred with the upload channel.')
    raise SystemExit(e)

# use upload URL to upload file if upload channel successful
if upload_channel.status_code == 201:
    uploadURL = upload_channel.json()["uploadUrl"]
    r = uploads.upload_file(uploadURL, upload_file)
    try:
        upload_response = dracoon.post(r)
    except core.requests.exceptions.RequestException as e:
        print('An error ocurred with the file upload.')
        raise SystemExit(e)

    # finalize upload or exit on error
    if upload_response.status_code == 201:
        params = {
            "resolutionStrategy": "autorename",
            "keepShareLinks": False,
            "fileName": FILENAME,
            "fileKey": enc_file_key,
            "userFileKeyList": { 
                "items": [
                {
                 "fileKey": enc_file_key,
                 "userId": user_id
                }
            ]
            }
        }
        r = uploads.finalize_upload(uploadURL, params)
        upload_channel = dracoon.put(r)

        print(f'File uploaded: {upload_channel.status_code}')
        print(f"Success: {FILENAME} uploaded to parent ID {TARGET}.")
        # error on uploading file
    else:
        print(f'Error uploading file: {upload_response.status_code}')
        print(f'Details: {upload_response.text}')
        # error on getting upload channel
else:
    print(f'Error finalizing upload: {upload_channel.status_code}')
    print(f'Details: {upload_channel.text}')

# get missing file keys
r = nodes.get_missing_file_keys(fileID=upload_channel.json()["id"], limit=10)

try:
    missing_keys_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    print('An error ocurred getting missing file keys.')
    raise SystemExit(e)

# get public key containers for all users (only filtered for one file, no further iteration necessary)
if missing_keys_response.status_code == 200:
    public_keys = missing_keys_response.json()["users"]

    missing_keys = []
    
    # encrypt file keys with public keys
    for user in public_keys:

        # populate list with missing file keys 
        missing_key = crypto.encrypt_file_key_public(plain_file_key=plain_file_key, public_key=user["publicKeyContainer"])
        missing_keys.append({
            "userId": user["id"],
            "fileKey": missing_key,
            "fileId": upload_channel.json()["id"]
        })
    
    params = {
        "items": missing_keys
    }

    r = nodes.set_file_keys(params)

    # set missing keys 
    try:
        set_keys_response = dracoon.post(r)
    except core.requests.exceptions.RequestException as e:
        print('An error ocurred setting missing file keys.')
        raise SystemExit(e)

    print(set_keys_response.request.body)
    print(set_keys_response.url)
    
    if set_keys_response.status_code == 204:
        print(f'Successfully added {len(missing_keys)} file keys.')
    else:
        print(f'Error setting file keys: {set_keys_response.status_code}')
        print(set_keys_response.text)