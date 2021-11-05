"""
Async DRACOON users adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/users

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""


import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType
from .users_models import CreateUser, SetUserAttributes, UpdateUser, UpdateUserAttributes

class DRACOONUsers:

    def __init__(self, dracoon_client: DRACOONClient):

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/users'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_user(self, user: CreateUser):

        payload = user.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res
    
    @validate_arguments
    async def get_users(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get user details for given user id
    @validate_arguments
    async def get_user(self, user_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update user's meta data for given user id
    @validate_arguments
    async def update_user(self, user_id: int, user_update: UpdateUser):
        
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        payload = user_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete user for given user id
    @validate_arguments
    async def delete_user(self, user_id: int):
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get user details for given user id
    @validate_arguments
    async def get_user_groups(self, user_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{user_id}/groups/?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get rooms in which user is last remaining admin (prevents user deletion!)
    @validate_arguments
    async def get_user_last_admin_rooms(self, user_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/last_admin_rooms'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get roles assigned to user
    @validate_arguments
    async def get_user_roles(self, user_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/roles'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get custom user attributes (key, value)
    @validate_arguments
    async def get_user_attributes(self, user_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{user_id}/userAttributes/?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # set custom user attributes (key, value)
    @validate_arguments
    async def delete_user_attribute(self, user_id: int, key: str):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/userAttributes/{key}'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update custom user attributes (key, value)
    @validate_arguments
    async def update_user_attributes(self, user_id: int, attributes: UpdateUserAttributes):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/userAttributes'
        payload = attributes.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# get all users
@validate_arguments
def get_users(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# create a user with given parameters
@validate_arguments
def create_user(params: CreateUser):
    api_call = {
        'url': '/users',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get user details for given user id
@validate_arguments
def get_user(userID: int):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update user's meta data for given user id
@validate_arguments
def update_user(userID: int, params: UpdateUser):
    api_call = {
        'url': '/users/' + str(userID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete user for given user id
@validate_arguments
def delete_user(userID: int):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get user details for given user id
@validate_arguments
def get_user_groups(userID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users/' + str(userID) + '/groups?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# get rooms in which user is last remaining admin (prevents user deletion!)
@validate_arguments
def get_user_last_admin_rooms(userID: int):
    api_call = {
        'url': '/users/' + str(userID) + '/last_admin_rooms',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get roles assigned to user
@validate_arguments
def get_user_roles(userID: int):
    api_call = {
        'url': '/users/' + str(userID) + '/roles',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get custom user attributes (key, value)
@validate_arguments
def get_user_attributes(userID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# set custom user attributes (key, value)
@validate_arguments
def set_user_attributes(userID: int, params: SetUserAttributes):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call


# update custom user attributes (key, value)
@validate_arguments
def update_user_attributes(userID: int, params: UpdateUserAttributes):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call






    
        