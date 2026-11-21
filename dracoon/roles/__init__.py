

import logging
from typing import List, Optional

from .responses import RoleGroupList, RoleUserList
from .models import GroupIds, UserIds
from dracoon.user.responses import RoleList
from dracoon.client import DRACOONClient
from dracoon.errors import ClientDisconnectedError, InvalidClientError


class DRACOONRoles:

    """
    API wrapper for DRACOON roles endpoint:
    Roles management
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.roles')
        
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/roles'
    
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
 
        else:
            self.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
        
        
    async def get_roles(self, raise_on_err: bool = False) -> Optional[RoleList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting roles failed.")
            return None
        
        return RoleList(**res.json())

    async def get_groups_with_role(self, role_id: int, raise_on_err: bool = False) -> Optional[RoleGroupList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting roles failed.")
            return None
        
        return RoleGroupList(**res.json())

    async def assign_groups_to_role(self, role_id: int, groups: GroupIds, raise_on_err: bool = False) -> Optional[RoleGroupList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'
        
        payload = groups.model_dump(exclude_unset=True)

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Assigning role failed.")
            return None
        
        return RoleGroupList(**res.json())
        

    async def remove_groups_from_role(self, role_id: int, groups: GroupIds, raise_on_err: bool = False) -> Optional[RoleGroupList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'
        
        payload = groups.model_dump(exclude_unset=True)

        res = await self.dracoon.request('DELETE', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Assigning role failed.")
            return None
        
        return RoleGroupList(**res.json())
            
    async def get_users_with_role(self, role_id: int, raise_on_err: bool = False) -> Optional[RoleUserList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting roles failed.")
            return None
        
        return RoleUserList(**res.json())

    async def assign_users_to_role(self, role_id: int, users: UserIds, raise_on_err: bool = False) -> Optional[RoleUserList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'
        
        payload = users.model_dump(exclude_unset=True)

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Assigning role failed.")
            return None
        
        return RoleUserList(**res.json())

    async def remove_users_from_role(self, role_id: int, users: UserIds, raise_on_err: bool = False) -> Optional[RoleUserList]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'
        
        payload = users.model_dump(exclude_unset=True)

        res = await self.dracoon.request('DELETE', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Assigning role failed.")
            return None
        
        return RoleUserList(**res.json())
    
    def make_user_group_ids(self, ids: List[int], is_user: bool = True):
        
        payload = {
            "ids": ids
        }
        
        if is_user:
            return UserIds(**payload)
        else:
            return GroupIds(**payload)
    