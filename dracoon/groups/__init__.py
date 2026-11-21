"""
Async DRACOON groups adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/groups

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 

"""

import logging
from typing import List, Optional
import urllib.parse

from dracoon.user.responses import RoleList
from dracoon.client import DRACOONClient
from dracoon.errors import ClientDisconnectedError, InvalidClientError
from .models import CreateGroup, Expiration, UpdateGroup
from .responses import Group, GroupList, GroupUserList, LastAdminGroupRoomList


class DRACOONGroups:

    """
    API wrapper for DRACOON groups endpoint:
    Group management - requires group manager role.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.groups')
        
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/groups'
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
    
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    async def create_group(self, group: CreateGroup, raise_on_err: bool = False) -> Optional[Group]:
        """ creates a new group """

        if self.raise_on_err:
            raise_on_err = True

        payload = group.model_dump(exclude_unset=True)

        res = await self.dracoon.request('POST', self.api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Creating group failed.")
            return None
        
        self.logger.info("Group created.")
        return Group(**res.json())

    def make_group(self, name: str, expiration: Expiration = None) -> CreateGroup:
        """ makes a group required for create_group() """

        group = {
            "name": name
        }
        
        if expiration: group["expiration"] = group

        return CreateGroup(**group)
    
    async def get_groups(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> Optional[GroupList]:
        """ list (all) groups """
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting groups failed.")
            return None
        
        self.logger.info("Retrieved groups.")
        return GroupList(**res.json())


    async def get_group(self, group_id: int, raise_on_err: bool = False) -> Optional[Group]:
        """ get user details for specific group (by id) """
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/{str(group_id)}'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting group failed.")
            return None
        
        self.logger.info("Retrieved group.")
        return Group(**res.json())


    async def update_group(self, group_id: int, group_update: UpdateGroup, raise_on_err: bool = False) -> Optional[Group]:
        """ update user details for specific group (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}'

        payload = group_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating group failed.")
            return None
        
        self.logger.info("Updated group.")
        return Group(**res.json())

    def make_group_update(self, name: str = None, expiration: Expiration = None) -> UpdateGroup:
        """ make a group update payload required for update_group() """
        group_update = {}

        if name: group_update["name"] = name
        if expiration: group_update["expiration"] = name

        return UpdateGroup(**group_update)

    async def delete_group(self, group_id: int, raise_on_err = False) -> None:
        """ delete specific user (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}'

        res = await self.dracoon.request('DELETE', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting group failed.")
            return None
        
        self.logger.info("Deleted group.")
        return None

    async def get_group_users(self, group_id: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> Optional[GroupUserList]:
        """ list all users for a specific group (by id) """
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/{group_id}/users?offset={str(offset)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting group users failed.")
            return None
        
        self.logger.info("Retrieved group users.")
        return GroupUserList(**res.json())

    async def get_group_last_admin_rooms(self, group_id: int, raise_on_err: bool = False) -> Optional[LastAdminGroupRoomList]:
        """ list all rooms, in which group is last admin (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/last_admin_rooms'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting group last admin rooms failed.")
            return None
        
        self.logger.info("Retrieved last admin group list.")
        return LastAdminGroupRoomList(**res.json())

    async def get_group_roles(self, group_id: int, raise_on_err: bool = False) -> Optional[RoleList]:
        """ get group roles for specific user (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/roles'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting group roles failed.")
            return None
        
        self.logger.info("Retrieved group roles list.")
        return RoleList(**res.json())

    async def add_group_users(self, group_id: int, user_list: List[int], raise_on_err: bool = False) -> Optional[Group]:
        """ bulk add a list of users to a group (by id) """
        if self.raise_on_err:
            raise_on_err = True
        
 
        api_url = self.api_url + f'/{str(group_id)}/users'

        payload = {
            "ids": user_list
        }

        res = await self.dracoon.request('POST', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Adding group users failed.")
            return None
        
        self.logger.info("Added group user(s).")
        return Group(**res.json())

    async def delete_group_users(self, group_id: int, user_list: List[int], raise_on_err: bool = False) -> Optional[Group]:
        """ bulk delete a list of users to a group (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(group_id)}/users'

        payload = {
            "ids": user_list
        }

        res = await self.dracoon.request('DELETE', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting group users failed.")
            return None
        
        self.logger.info("Deleted group users(s).")
        return Group(**res.json())