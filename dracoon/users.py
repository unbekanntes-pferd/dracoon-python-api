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


from typing import List
import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType
from .users_models import AttributeEntry, CreateUser, Expiration, SetUserAttributes, UpdateUser, UpdateUserAttributes, UserAuthData
from .user_responses import AttributesResponse, LastAdminUserRoomList, RoleList, UserData, UserGroupList, UserList

class DRACOONUsers:

    """
    API wrapper for DRACOON users endpoint:
    User management - requires user manager role.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/users'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_user(self, user: CreateUser) -> UserData:
        """ creates a new user """

        payload = user.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Creating user in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UserData(**res.json())

    def make_local_user(self, first_name: str, last_name: str, email: str, login: str = None,
                        language: str = None, notify: bool = None, expiration: Expiration = None, phone: str = None) -> CreateUser:
        """ makes a new local (basic) user required for create_user() """
        auth = self.make_auth_data(method='basic')

        user = {
            "firstName": first_name,
            "lastName": last_name, 
            "email": email,
            "userName": email,
            "authData": auth  
        }

        if login: user["userName"] = login
        if language: user["receiverLanguage"] = language
        if notify is not None: user["notifyUser"] = notify
        if expiration: user["expiration"] = expiration
        if phone: user["phone"] = phone

        return CreateUser(**user)

    def make_oidc_user(self, first_name: str, last_name: str, email: str, login: str, oidc_id: int, 
                       language: str = None, notify: bool = None, expiration: Expiration = None, phone: str = None) -> CreateUser:
        """ makes a new OpenID Connect (openid) user required for create_user() """
        auth = self.make_auth_data(method='openid', oidc_id=oidc_id, login=login)
           
        user = {
            "firstName": first_name,
            "lastName": last_name, 
            "email": email,
            "authData": auth  
        }    

        if language: user["receiverLanguage"] = language
        if notify is not None: user["notifyUser"] = notify
        if expiration: user["expiration"] = expiration
        if phone: user["phone"] = phone
        
        return CreateUser(**user)

    def make_ad_user(self, first_name: str, last_name: str, email: str, login: str, ad_id: int,
                     language: str = None, notify: bool = None, expiration: Expiration = None, phone: str = None) -> CreateUser:
        """ makes a new Active Directory (active_directory) user required for create_user() """
        auth = self.make_auth_data(method='active_directory', ad_id=ad_id, login=login)
        
        user = {
            "firstName": first_name,
            "lastName": last_name, 
            "email": email,
            "authData": auth,
            "userName": login 
        }    

        if language: user["receiverLanguage"] = language
        if notify is not None: user["notifyUser"] = notify
        if expiration: user["expiration"] = expiration
        if phone: user["phone"] = phone   
        
        return CreateUser(**user)

    def make_user_update(self, first_name: str = None, last_name: str = None, email: str = None, user_name: str = None, 
                         locked: bool = None, phone: str = None, expiration: Expiration = None, language: str = None,
                         auth_data: UserAuthData = None, non_member_viewer: bool = None) -> UpdateUser:
        """ makes an user update payload required for update_user() """
        user_update = {

            }
        
        if language: user_update["receiverLanguage"] = language
        if locked is not None: user_update["isLocked"] = locked
        if expiration: user_update["expiration"] = expiration
        if phone: user_update["phone"] = phone
        if first_name: user_update["firstName"] = first_name  
        if last_name: user_update["lastName"] = last_name   
        if non_member_viewer is not None: user_update["isNonmemberViewer"] = non_member_viewer   
        if auth_data: user_update["authData"] = auth_data   
        if email: user_update["email"] = email 
        if user_name: user_update["userName"] = user_name

        return UpdateUser(**user_update)

        
    def make_auth_data(self, method: str, login: str = None, password: str = None, 
                      change_password: bool = None, ad_id: int = None, oidc_id: int = None) -> UserAuthData:
        """ makes authentication data required for user creation / modification """
        auth =  {
            "method": method
        }

        if login: auth["login"] = login
        if password: auth["password"] = password
        if change_password is not None: auth["mustChangePassword"] = change_password
        if ad_id: auth["adConfigId"] = ad_id
        if oidc_id: auth["oidConfigId"] = oidc_id

        return UserAuthData(**auth)


    @validate_arguments
    async def get_users(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None) -> UserList:     
        """ list (all) users """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Listing users in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UserList(**res.json())

    # get user details for given user id
    @validate_arguments
    async def get_user(self, user_id: int) -> UserData:
        """ get user details for specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Listing user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UserData(**res.json())

    # update user's meta data for given user id
    @validate_arguments
    async def update_user(self, user_id: int, user_update: UpdateUser) -> UserData:
        """ update user details for specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        payload = user_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UserData(**res.json())

    # delete user for given user id
    @validate_arguments
    async def delete_user(self, user_id: int) -> None:
        """ delete specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # get user details for given user id
    @validate_arguments
    async def get_user_groups(self, user_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None) -> UserGroupList:
        """ list all groups for a specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{user_id}/groups/?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting groups for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UserGroupList(**res.json())

    # get rooms in which user is last remaining admin (prevents user deletion!)
    @validate_arguments
    async def get_user_last_admin_rooms(self, user_id: int) -> LastAdminUserRoomList:
        """ list all rooms, in which user is last admin (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/last_admin_rooms'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting last admin rooms for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return LastAdminUserRoomList(**res.json())

    # get roles assigned to user
    @validate_arguments
    async def get_user_roles(self, user_id: int) -> RoleList:
        """ get user roles for specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/roles'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting roles for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')


        return RoleList(**res.json())

    # get custom user attributes (key, value)
    @validate_arguments
    async def get_user_attributes(self, user_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None) -> AttributesResponse:
        """ get custom user attributes for a specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{user_id}/userAttributes/?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting user attributes for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return AttributesResponse(**res.json())

    # set custom user attributes (key, value)
    @validate_arguments
    async def delete_user_attribute(self, user_id: int, key: str) -> None:
        """ delete custom user attribute for a specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/userAttributes/{key}'

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting attribute {key} for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # update custom user attributes (key, value)
    @validate_arguments
    async def update_user_attributes(self, user_id: int, attributes: UpdateUserAttributes) -> UserData:
        """ create / update custom user attribute for a specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(user_id)}/userAttributes'
        payload = attributes.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating attributes for user {user_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')
        
        return UserData(**res.json())

    def make_custom_user_attribute(self, key: str, value: str) -> AttributeEntry:
        """ make a custom user attribute required for update_user_attributes() """
        return AttributeEntry(**{
            "key": key,
            "value": value
        })

    def make_attributes_update(self, list: List[AttributeEntry]) -> UpdateUserAttributes:
        """ consolidate mulitple attributes into list - required for update_user_attributes() """
        return UpdateUserAttributes(**{
            "items": list
        })

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






    
        