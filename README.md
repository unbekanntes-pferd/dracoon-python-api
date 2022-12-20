
  <h3 align="center">DRACOON-PYTHON-API</h3>

  <p align="center">
    Python connector to DRACOON API
    <br />
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/unbekanntes-pferd/DRACOON-PYTHON-API/issues">Report Bug</a>
  </p>
</p>

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [About the Project](#about-the-project)
  * [Built With](#built-with)
* [Getting Started](#getting-started)
  * [Prerequisites](#prerequisites)
  * [Installation](#installation)
* [Usage](#usage)
* [Roadmap](#roadmap)
* [Contributing](#contributing)
* [License](#license)



<!-- ABOUT THE PROJECT -->
## About The Project
__Disclaimer: this is an unofficial repo and is not supported by DRACOON__<br>
This package provides a wrapper for the DRACOON API including full crypto support. 
DRACOON is a cloud storage product / service (SaaS) by DRACOON GmbH (http://dracoon.com). 
DRACOON API documentation can be found here (Swagger UI):

https://dracoon.team/api/

### Built With

* [Python 3.9.0](https://www.python.org/)
* [httpx module](https://www.python-httpx.org/)
* [cryptography](https://cryptography.io/en/latest/)
* [pydantic](https://pydantic-docs.helpmanual.io/)

[List all dependencies](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/requirements.txt)

<!-- GETTING STARTED -->
## Getting Started

To get started, create a virtual environment in Python and install the dracoon package:
```bash
virtualenv <DIR>
source <DIR>/bin/activate 
python3 -m pip install dracoon
```

### Prerequisites

You will need a working Python 3 installation - check your version:
* Python
```bash
python3 --version
```

### Installation

1. Install the package from PyPi
```bash
python3 -m pip install dracoon
```

<!-- USAGE EXAMPLES -->
## Usage
### Import DRACOON
```Python
from dracoon import DRACOON
```

This is the main class and contains all other adapters to access DRACOON API endpoints. 
The object contains a client (DRACOONClient) which handles all http connections via httpx (async). 


### Object creation
```Python
dracoon = DRACOON(base_url, client_id, client_secret)
```

* _client_id_: please register your OAuth app or use dracoon_legacy_scripting (default)
* _client_secret_: please register your OAuth app or use dracoon_legacy_scripting - secret is an empty string (no secret)
* _base_url_: Your DRACOON URL instance (e.g. https://dracoon.team)

#### Optional settings
You can additionally configure the logs for any script using the following optional parameters:
* _log_stream_: default is set to False – when set to True, will output the logs to console / terminal (stderr)
* _log_level_: default is set to logging.INFO – if required, can be changed to e.g. logging.DEBUG (this will contain senstive information e.g. names of created objects!). In order to use the log level, import logging module
* _log_file_: default is set to './dracoon.log' (based on cwd of the running script!) – you can use any path with write access to log
* _raise_on_err_: default is set to False – if set to True, any HTTP error (4xx or higher) will raise an error and stop the script / application

Full parameters:
```Python
dracoon = DRACOON(base_url, client_id, client_secret, log_level, log_stream, log_file, raise_on_err)
```

A note to raising on errors: You can set the raise_on_err flag individually for any adapter method (e.g. nodes.get_nodes(raise_on_err=True)) to ensure the app breaks in case an error occurs. 


### Authentication

#### Password flow

```Python
connection = await dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
```

The connection result contains the tokens (access and refresh, including validity).

You need pass one of the supported OAuth2 connection types. 
To access the enums, import OAuth2ConnectionType:

```Python
from dracoon import DRACOON, OAuth2Connectiontype
```

Please note: you can only authenticate if OAuth app is correctly configured. Only local accounts (including Active Directory) can be used via password flow.
Full example: [Login via password flow](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/login_password_flow.py)

#### Authorization code flow
```Python
print(dracoon.get_code_url())
auth_code = input('Enter auth code:')
connection = await dracoon.connect(auth_code=auth_code)
```
If you do not provide a connection type, the default will be auth code.
You should prompt (or fetch) the auth code via the respective url.
Full example: [Login via auth code](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/login_auth_code_flow.py)

Please note: you can only authenticate if OAuth app is correctly configured. You will need a custom app with authorization code flow enabled and you will need to set your redirect uri to https://your.domain.com/oauth/callback 

#### Test connection
```Python
connected = dracoon.test_connection()
```
This will provide a true / false result depending on the connection.
If no flag is set, this will just check if the access token is valid based on the token validity.
In order to test the connection with a request, is the test flag:

#### Test connection
```Python
connected = dracoon.test_connection(test=True)
```

An authenticated ping is used to verify the tokens are valid.

#### Refresh token

All methods check for access token validity and fetch new tokens, if the access tokens expire.
Therefore it should not be necessary to manually request it.

You can manually use the refresh token auth as follows:

```Python
connection = await dracoon.client.connect(OAuth2ConnectionType.refresh_token)
```

Every connect process will update the connection.


#### Log out
```Python
await dracoon.logout()
```
This will revoke both access and refresh tokens.


### Send requests

1. You can access specific API endpoints by accessing the related adapter, e.g. for users, once you have connected:

```Python
result = await dracoon.users.get_users()
```

Please note: 
* GET requests are limited to returning 500 items. Therefore all such requests contain an offset parameter (default is 0)
* Providing a filter or sorting is optional - see API documentation and examples on usage – filter, sort or any other query parameter can be passed as parameter in any method
* Raising on errors: Default is set to False – if needed, you can use the raise_on_err flag to stop for responses with HTTP status code 4xx or higher
* If you do not connect the client, the adapters are not instantiated and 
cannot be accessed!
* All (!) calls are async methods and need to be awaited

Available adapters:

```Python
dracoon.config  # config API including webhooks
dracoon.users  # users management
dracoon.groups # groups management
dracoon.user # user account and keypair setup
dracoon.nodes # nodes (up- and download including S3 direct up)
dracoon.shares # shares and file requests
dracoon.uploads # upload API
dracoon.reports # new reporting API
dracoon.eventlog # old eventlog API
```


2. This package contains type hints and includes models for all payloads and responses (updates and create payloads).
To faciliate compliant object creation, there are several helper methods which can be found via make_, e.g.:

```Python
room = dracoon.nodes.make_room(...)
```

This helps finding the right parameters and building objects that are compliant with the DRACOON models.

#### Aynchronous requests

With httpx this package support full async request handling. This means all methods are coroutines which can be awaited.
You can use any runtime supported by httpx, e.g. asyncio (which comes with Python3).

In order to send requests asynchronously, you can use ayncio.gather() – example:

```Python
user1_res = dracoon.users.create_user(user1)
user2_res = dracoon.users.create_user(user2)
user3_res = dracoon.users.create_user(user3)
...

users = await asyncio.gather(user1_res, user2_res, user3_res, ...)

```

The result is completely typed and returns a tuple with the responses in the order you sent the request:
For users[0] you receive user_1_res and so on.

Caution: It is not recommended to use massive async requests for creating objects (e.g. creating rooms) or permissions based operations, as this might cause unexpected behaviour / errors.

For these cases, use small batches (e.g. 2 - 3 requests) to process requests faster without compromising the DRACOON API.

Example for batches:

```Python
room1_res = dracoon.nodes_create_room(room1)
room2_res = dracoon.nodes_create_room(room2)
room3_res = dracoon.nodes_create_room(room3)

...

rooms = await asyncio.gather(room1_res, room2_res, room3_res, ...)

for i in range(0, len(rooms) + 3, 3):
  rooms_res = await asyncio.gather(rooms[i:i+3])

```

## Cryptography

DRACOON cryptography is fully supported by the package. In order to use it, import the relevant functions or en- and decryptors:

```Python
from dracoon.crypto import create_plain_userkeypair
from dracoon.crypto import create_file_key
```

### Create a new keypair

The account adapter (user) includes a method to set a new keypair:

```Python
dracoon.user.set_keypair(secret)

```
A new keypair will be generated (4096bit RSA asymmetric).
Prior to setting a new keypair you always need to delete the old one!
Please note: Deleting a keypair can cause data loss.

### Getting your (plain) keypair

In order to work with encrypted rooms you will need to access your keypair:

```Python
await dracoon.get_keypair(secret=secret)

```
This method of the main API wrapper will accept a secret (that you need to pass or prompt) returns the plain keypair and stores in in 
the client for the current session.


### En- and decode on the fly (in memory)

For smaller payload you can directly use the functions returning either
plain or encrypted bytes like this:

```Python
plain_bytes = decrypt_bytes(enc_data, plain_file_key)
enc_bytes = encrypt_bytes(plain_data, plain_file_key)

```

### Chunking

For larger files it is recommended to encrypt (and upload) in chunks.
An example of encryptor usage:

```Python
dracoon_cipher = FileEncryptionCipher(plain_file_key=plain_file_key)
enc_chunk = dracoon_cipher.encode_bytes(chunk)
last_data, plain_file_key = dracoon_cipher.finalize()

```
You can instantiate an encryptor / decryptor by passing a plain file key.
When finalizing, you need to add the last data to the last chunk.
The result of the completed encryption is an updated plain_file_key with a specific tag.

Hint: You do not need to implement the upload process and can directly use full methods in the uploads adapter (see next chapter).

## Uploads

The nodes and uploads adapters include full methods to upload data to DRACOON and includes chunking and encryption support.
Implementing the upload with respective calls is not recommended - please use the main wrapper (see example below) instead.

Here is an example of uploading a file to an encrypted room with only a few lines of code:

```Python

    source = '/Example/Path/test.mov'
    target = '/Example/Target/'
    
    await dracoon.upload(file_path=source, target_path=target, display_progress=True)
    
```

The default chunk size is 32 MB but can be passed as an option (chunksize, in bytes).
If needed, the progress bar can be displayed (see example - by setting to true) - default (or when ommitted) is false, so no progress is displayed.

The main API wrapper includes a method that includes upload for encrypted and unencrypted files.
Full example: [File upload](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/upload.py)

## Downloads

The downloads adapter includes full methods to download data from DRACOON including chunking and encryption support.

In order to download a file, generate a download url and use the relevant method:

```Python
res = await self.nodes.get_download_url(node_id=node_id)
download_url = res.downloadUrl

await.self.downloads.download_unencrypted(download_url=download_url, target_path=target_path, node_info=node_info)
    
```

To get the node information based on a path, you can use the following method:

```Python
node_info = await self.nodes.get_node_from_path(file_path)
```

In order to download encrypted files, you will need to unlock your keypair and retrieve your file key:

```Python
plain_keypair = dracoon.get_keypair(secret)
# get node id via node info (see above)
file_key = await self.nodes.get_user_file_key(node_id)
plain_file_key = decrypt_file_key(file_key, plain_keypair)
```

As with uploads, the main wrapper has a method which handles encryption, keypair and file key – above steps do not need to be performed if not needed.
Instead, use the main wrapper:


```Python

target = '/Example/Target'
source = '/DEMO/testfile.bin'
await dracoon.download(file_path=file, target_path=target)

```

Full example: [Download files](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/download.py)


## Examples

_For examples, check out the example files:_<br>

* [Login via password flow](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/login_password_flow.py)
* [Login via auth code](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/login_auth_code_flow.py)
* [Create a user](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/create_user.py)
* [Set up personal rooms](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/personal_rooms.py)
* [Process pending group assignments](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/pending_assignments.py)
* [Set a new keypair](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/create_new_keypair.py)
* [Upload file](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/upload.py)
* [Download files](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/download.py)

<!-- ROADMAP -->
## Roadmap
* Add branding API 

<!-- LICENSE -->
## License

Distributed under the Apache License. See [LICENSE](/LICENSE) for more information.
