"""
Async DRACOON users adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/groups

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 

"""

from typing import List
import httpx
from pydantic import validate_arguments

from .groups_responses import Group, GroupList, GroupUserList, LastAdminGroupRoomList
from .user_responses import RoleList

from .core import DRACOONClient, OAuth2ConnectionType
from .groups_models import CreateGroup, Expiration, UpdateGroup
from .core_models import IDList
import logging

class DRACOONGroups:

    """
    API wrapper for DRACOON groups endpoint:
    Group management - requires group manager role.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/groups'
            self.logger = logging.getLogger('dracoon.groups')
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

            self.logger.debug("DRACOON groups adapter created.")
        
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ValueError('DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_group(self, user: CreateGroup, raise_on_err: bool = False) -> Group:
        """ creates a new group """

        if self.raise_on_err:
            raise_on_err = True

        payload = user.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating group failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Group created.")
        return Group(**res.json())

    def make_group(self, name: str, expiration: Expiration = None) -> CreateGroup:
        """ makes a group required for create_group() """

        group = {
            "name": name
        }
        
        if expiration: group["expiration"] = group

        return CreateGroup(**group)
    
    @validate_arguments
    async def get_groups(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> GroupList:
        """ list (all) groups """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
        
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting groups failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved groups.")
        return GroupList(**res.json())


    @validate_arguments
    async def get_group(self, group_id: int, raise_on_err: bool = True) -> Group:
        """ get user details for specific group (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting group failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved group.")
        return Group(**res.json())


    @validate_arguments
    async def update_group(self, group_id: int, group_update: UpdateGroup, raise_on_err: bool = False) -> Group:
        """ update user details for specific group (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}'

        payload = group_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating group failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated group.")
        return Group(**res.json())

    def make_group_update(self, name: str = None, expiration: Expiration = None) -> UpdateGroup:
        """ make a group update payload required for update_group() """
        group_update = {}

        if name: group_update["name"] = name
        if expiration: group_update["expiration"] = name

        return UpdateGroup(**group_update)

    @validate_arguments
    async def delete_group(self, group_id: int, raise_on_err = False) -> None:
        """ delete specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting group failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted group.")
        return None

    # get user details for given user id
    @validate_arguments
    async def get_group_users(self, group_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> GroupUserList:
        """ list all users for a specific group (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{group_id}/users/?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting group users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved group users.")
        return GroupUserList(**res.json())

    # get rooms in which group is last remaining admin (prevents user deletion!)
    @validate_arguments
    async def get_group_last_admin_rooms(self, group_id: int, raise_on_err: bool = False) -> LastAdminGroupRoomList:
        """ list all rooms, in which group is last admin (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/last_admin_rooms'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting group last admin rooms failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved last admin group list.")
        return LastAdminGroupRoomList(**res.json())

    # get roles assigned to group
    @validate_arguments
    async def get_group_roles(self, group_id: int, raise_on_err: bool = False) -> RoleList:
        """ get group roles for specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/roles'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting group roles failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved group roles list.")
        return RoleList(**res.json())

    @validate_arguments
    async def add_group_users(self, group_id: int, user_list: List[int], raise_on_err: bool = False) -> Group:
        """ bulk add a list of users to a group (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/users'

        payload = {
            "ids": user_list
        }

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Adding group users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Added group user(s).")
        return Group(**res.json())

    @validate_arguments
    async def delete_group_users(self, group_id: int, user_list: List[int], raise_on_err: bool = False) -> Group:
        """ bulk delete a list of users to a group (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/users'

        payload = {
            "ids": user_list
        }

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting group users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted group users(s).")
        return Group(**res.json())


"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# get list of groups
@validate_arguments
def get_groups(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/groups?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a group with given parameters
@validate_arguments
def create_group(params: CreateGroup):
    api_call = {
        'url': '/groups',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }

    return api_call

# get group details for given group id
@validate_arguments
def get_group(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update group's meta data for given group id
@validate_arguments
def update_group(groupID: int, params: UpdateGroup):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete user for given user id
@validate_arguments
def delete_group(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get rooms in which group is last remaining admin (prevents user deletion!)
@validate_arguments
def get_group_last_admin_rooms(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/last_admin_rooms',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get roles assigned to group
@validate_arguments
def get_group_roles(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/roles',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get group users
@validate_arguments
def get_group_users(groupID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/groups/' + str(groupID) + '/users?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# update assigned users (array of user ids) to a group with given group id
@validate_arguments
def update_group_users(userIDs: List[int], groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/users',
        'body': {
            "ids": userIDs
        },
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# delete assigned users (array of user ids) from a group with given group id
@validate_arguments
def delete_group_users(params: IDList, groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/users',
        'body': params,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

