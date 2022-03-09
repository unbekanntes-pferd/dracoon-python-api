# ---------------------------------------------------------------------------#
# DRACOON API Python examples
# Update user keypair
# Requires dracoon package
# Author: Octavio Simone, 21.07.2021
# ---------------------------------------------------------------------------#

from dracoon import crypto
from dracoon.crypto.models import UserKeyPairVersion
from dracoon import core, user
import getpass

# replace with client id from OAuth app - for Cloud you can use dracoon_legacy_scripting if enabled in apps
clientID = 'xxx'
# replace with client secret - dracoon_legacy_scripting has no secret, it can be omitted as parameter
clientSecret = 'xxxx'
baseURL = 'https://demo.dracoon.com'  # replace with own DRACOON url


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

# set keypair (2048bit version used here, can be replaced by UserKeyPairVersion.RSA4096.value for current 4096 bit length)
plain_keypair = crypto.create_plain_userkeypair(version=UserKeyPairVersion.RSA2048.value)

# obtain keypair decryption secret 
RO_crypto_password = getpass.getpass('Set encryption password: ')

# encrypt keypair 
encrypted_keypair = crypto.encrypt_private_key(secret=RO_crypto_password, plain_key=plain_keypair)

r = user.delete_user_keypair()

try:
    keypair_response = my_dracoon.delete(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if keypair_response.status_code == 200:
    print('Deleted old keypair: ' + str(keypair_response.status_code))
else:
    print(keypair_response.status_code)
    print(keypair_response.text)

r = user.set_user_keypair(encrypted_keypair)

try:
    keypair_response = my_dracoon.post(r)
except core.requests.exceptions.RequestException as e:
    raise SystemExit(e)

if keypair_response.status_code == 204:
    print('Updated keypair: ' + str(keypair_response.status_code))
else:
    print(keypair_response.status_code)
    print(keypair_response.text)
