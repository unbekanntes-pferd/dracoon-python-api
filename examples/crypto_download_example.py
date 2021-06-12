# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Download encrypted file and decrypt
# WARNING: no chunking, this is a simple example
# For large files, download and decryption should be chunked to avoid 
# trying to load the complete file into memory
# Requires dracoon package
# Author: Octavio Simone, 12.06.2021
# ---------------------------------------------------------------------------#

import getpass
import requests
from dracoon import core, nodes, crypto, user

# base settings

client_id = 'xxxxx'
client_secret = 'xxxxx'
base_url = 'https://dracoon.team'

# replace with node id
FILE_ID = 999

# initialize dracoon
dracoon = core.Dracoon(clientID=client_id, clientSecret=client_secret)
dracoon.set_URLs(baseURL=base_url)

# authenticate
print(dracoon.get_code_url())
auth_code = input('Enter auth code:')

dracoon.oauth_code_auth(code=auth_code)

# get file information (file name)

r = nodes.get_node(FILE_ID)

try:
    file_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)


if file_response.status_code == 200:
    file_name = file_response.json()["name"]
    print(f'Target file: {file_name}')
else: 
    print('Could not retrieve file information')


# get file key for given file id
r = nodes.get_user_file_key(fileID=FILE_ID)

try:
    file_key_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)


if file_key_response.status_code == 200:
    file_key = file_key_response.json()
    print(f'Retrieved file key for: {file_name}')
else: 
    print('Could not retrieve file key')

# get user keypair

r = user.get_user_keypair()

try:
    keypair_response = dracoon.get(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if keypair_response.status_code == 200:
    enc_keypair = keypair_response.json()
    print(f'Retrieved user keypair')
else: 
    print('Could not retrieve keypair')

# prompt for decryption password
decrypt_password = getpass.getpass('Enter decryption password:')

# get plain keypair (private key)
plain_keypair = crypto.decrypt_private_key(secret=decrypt_password, keypair=enc_keypair)

# get plain file key
plain_key = crypto.decrypt_file_key(fileKey=file_key, keypair=plain_keypair)

# get download URL
r = nodes.get_download_url(FILE_ID)

try:
    download_response = dracoon.post(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)
else: 
    print(download_response.status_code)
    print(download_response.text)

download_url = None

if download_response.status_code == 200:
    download_url = download_response.json()["downloadUrl"]
    print(f'Retrieved download URL for {file_name}')
# download encrypted bytes
else: 
    print(download_response.status_code)
    print(download_response.text)

# WARNING: file is loaded into memory. Chunking needs to be implemented for large files
try:
    downloaded_bytes = requests.get(download_url)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

# decrypt bytes
decrypted_bytes = crypto.decrypt_bytes(enc_data=downloaded_bytes.content, plain_file_key=plain_key)

# write file to path
open(file_name, 'wb').write(decrypted_bytes)