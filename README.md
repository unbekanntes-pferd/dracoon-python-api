
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

* _client_id_; please register your OAuth app or use dracoon_legacy_scripting (default)
* _client_secret_; please register your OAuth app or use dracoon_legacy_scripting - secret is an empty string (no secret)
* _base_url_: Your DRACOON URL instance (e.g. https://dracoon.team)


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
Full example: [Login via password flow](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_login_password_flow.py)

#### Authorization code flow
```Python
print(dracoon.get_code_url())
auth_code = input('Enter auth code:')
connection = await dracoon.connect(auth_code=auth_code)
```
If you do not provide a connection type, the default will be auth code.
You should prompt (or fetch) the auth code via the respective url.
Full example: [Login via auth code](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_login_auth_code_flow.py)

Please note: you can only authenticate if OAuth app is correctly configured. You will need a custom app with authorization code flow enabled and you will need to set your redirect uri to https://your.domain.com/oauth/callback 

#### Test connection
```Python
connected = dracoon.test_connection()
```
This will provide a true / false result depending on the connection.
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
* Providing a filter is optional - see API documentation and examples on usage
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


2. This package contains type hints and includes models for all payloads (updates and create payloads).
To faciliate compliant object creation, there are several helper methods which can be found via make_, e.g.:

```Python
room = dracoon.nodes.make_room(...)
```

This helps finding the right parameters and building objects that are compliant with the DRACOON models.

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

The uploads adapter includes full methods to upload data to DRACOON and includes chunking and encryption support.

Here is an example of uploading a file to an encrypted room with only a few lines of code:

```Python
upload_channel = CreateUploadChannel(parentId=9999, name=file_path.split('/')[-1])

res = await dracoon.nodes.create_upload_channel(upload_channel=upload_channel)
channel_res = res.json()

res = await dracoon.uploads.upload_encrypted(file_path=file_path, target_id=9999, upload_channel=channel_res, plain_keypair=plain_keypair)
    
```

The default chunk size is 5 MB but can be passed as an option (chunksize, in bytes).

The main API wrapper includes a method that includes upload for encrypted and unencrypted files.
Full example: [File upload](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_upload.py)

## Downloads

The downloads adapter includes full methods to download data from DRACOON including chunking and encryption support.

In order to download a file, generate a download url and use the relevant method:

```Python
res = await self.nodes.get_download_url(node_id=node_id)
download_url = res.json()["downloadUrl"]

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

As with uploads, the main wrapper has a method which handles encryption, keypair and file key.
Full example: [Download files](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_download.py)


## Examples

_For examples, check out the example files:_<br>

* [Login via password flow](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_login_password_flow.py)
* [Login via auth code](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_login_auth_code_flow.py)
* [Create a user](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_create_user.py)
* [Set a new keypair](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_create_new_keypair.py)
* [Upload file](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_upload.py)
* [Download files](https://github.com/unbekanntes-pferd/dracoon-python-api/blob/master/examples/async_download.py)

<!-- ROADMAP -->
## Roadmap

* Add S3 direct upload
* Add branding API 
* Error handling, testing coverage
* Complete all types (update to data classes, remove pydantic, return objects)

<!-- LICENSE -->
## License

Distributed under the Apache License. See [LICENSE](/LICENSE) for more information.
