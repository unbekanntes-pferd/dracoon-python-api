"""
Async DRACOON users adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/user

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 
All requests with bodies use generic params variable to pass JSON body

"""

import httpx
import logging
from pydantic import validate_arguments

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.crypto import create_plain_userkeypair, encrypt_private_key
from dracoon.crypto.models import UserKeyPairContainer, UserKeyPairVersion
from dracoon.errors import ClientDisconnectedError, InvalidClientError, InvalidArgumentError
from .models import UpdateAccount, UserAccount




class DRACOONUser:
    """
    API wrapper for DRACOON user endpoint:
    Account information and management (user profile)
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
         
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid DRACOON client format.')
        
        self.logger = logging.getLogger('dracoon.user')
        
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/user'
            
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
            self.logger.debug("DRACOON user adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')


    # get account information for current user
    @validate_arguments
    async def get_account_information(self, more_info: bool = False, raise_on_err: bool = False) -> UserAccount:
        """ returns account information for authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        try:
            api_url = self.api_url + f'/account/?more_info={str(more_info).lower()}'
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting account information failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved user account.")
        return UserAccount(**res.json())

    # update account information for current user
    @validate_arguments
    async def update_account_information(self, account_update: UpdateAccount, raise_on_err: bool = False) -> UserAccount:
        """ updates account information for authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/account'

        payload = account_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating account information failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated user account.")
        return UserAccount(**res.json())

    def make_account_update(self, user_name: str = None, acceptEULA: bool = None, first_name: str = None, last_name: str = None, email: str = None, 
                            phone: str = None, language: str = None) -> UpdateAccount:
        """ creates account information update payload – required for update_account_information() """
        account_update = {}

        if acceptEULA == False:
            raise InvalidArgumentError(message="EULA acceptance cannot be undone.")

        if language: account_update["language"] = language
        if phone: account_update["phone"] = phone
        if first_name: account_update["firstName"] = first_name  
        if last_name: account_update["lastName"] = last_name    
        if email: account_update["email"] = email 
        if acceptEULA is not None: account_update["acceptEULA"] = acceptEULA
        if user_name: account_update["userName"] = user_name

        return UpdateAccount(**account_update)

    # get user keypair (encrypted)
    @validate_arguments
    async def get_user_keypair(self, version: UserKeyPairVersion = None, raise_on_err: bool = False) -> UserKeyPairContainer:
        """ returns encrypted user keypair (if present) for authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/account/keypair'
        if version != None: api_url += '/?version=' + version.value

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting user keypair failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved user keypair.")
        return UserKeyPairContainer(**res.json())

    # set user keypair 
    @validate_arguments
    async def set_user_keypair(self, secret: str, version: UserKeyPairVersion = UserKeyPairVersion.RSA4096, raise_on_err: bool = False) -> None:
        """ sets encrypted user keypair protected with secret (if none present) for authenticated user """
        plain_keypair = create_plain_userkeypair(version=version)
        encrypted_keypair = encrypt_private_key(secret=secret, plain_key=plain_keypair)

        if self.raise_on_err:
            raise_on_err = True
        
        payload = encrypted_keypair.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/account/keypair'

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Setting user keypair failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Set user keypair.")
        return None

    # delete user keypair 
    @validate_arguments
    async def delete_user_keypair(self, version: UserKeyPairVersion = None, raise_on_err: bool = False) -> None:
        """ deletes encrypted user keypair (if present) for authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/account/keypair'
        if version != None: api_url += '/?version=' + version.value

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting user keypair failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted user keypair.")
        return None
