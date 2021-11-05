"""
Async DRACOON users adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/user

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 
All requests with bodies use generic params variable to pass JSON body

"""


import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType
from .user_models import UpdateAccount
from .crypto_models import UserKeyPairContainer, UserKeyPairVersion
from .crypto import create_plain_userkeypair, encrypt_private_key


class DRACOONUser:

    def __init__(self, dracoon_client: DRACOONClient):

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/user'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')


    # get account information for current user
    @validate_arguments
    async def get_account_information(self, more_info: bool = False):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            api_url = self.api_url + f'/account/?{str(more_info).lower()}'
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update account information for current user
    @validate_arguments
    async def update_account_information(self, account_update: UpdateAccount):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/account'

        payload = account_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res


    # get user keypair (encrypted)
    @validate_arguments
    async def get_user_keypair(self, version: UserKeyPairVersion = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/account/keypair'
        if version != None: api_url += '/?version=' + version.value

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res


    # set user keypair 
    @validate_arguments
    async def set_user_keypair(self, secret: str, version: UserKeyPairVersion = UserKeyPairVersion.RSA4096):

        plain_keypair = create_plain_userkeypair(version=version.value)
        encrypted_keypair = encrypt_private_key(secret=secret, plain_key=plain_keypair)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/account/keypair'

        try:
            res = await self.dracoon.http.post(url=api_url, json=encrypted_keypair)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete user keypair 
    @validate_arguments
    async def delete_user_keypair(self, version: UserKeyPairVersion = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/account/keypair'
        if version != None: api_url += '/?version=' + version.value

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# get account information for current user
@validate_arguments
def get_account_information(more_info: bool = False):

    api_call = {
        'url': '/user/account?more_info=' + str(more_info).lower(),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    return api_call

# update account information for current user
@validate_arguments
def update_account_information(params: UpdateAccount):

    api_call = {
        'url': '/user/account',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    
    return api_call

# get user keypair (encrypted)
@validate_arguments
def get_user_keypair(version: UserKeyPairVersion = None):

    api_call = {
        'url': '/user/account/keypair',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if version != None: api_call["url"] += '?version=' + version.value

    return api_call

# set user keypair 
@validate_arguments
def set_user_keypair(params: UserKeyPairContainer):

    api_call = {
        'url': '/user/account/keypair',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }

    return api_call

# delete user keypair 
@validate_arguments
def delete_user_keypair(version: UserKeyPairVersion = None):

    api_call = {
        'url': '/user/account/keypair',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }

    if version != None: api_call["url"] += '?version=' + version.value


    return api_call
