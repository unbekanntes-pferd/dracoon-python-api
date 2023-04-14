

import logging
from typing import List
import httpx
from tenacity import retry

from .responses import RoleGroupList, RoleUserList
from .models import GroupIds, UserIds
from dracoon.user.responses import RoleList
from dracoon.client import RETRY_CONFIG, DRACOONClient
from dracoon.client.models import OAuth2ConnectionType
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
        
        
    @retry(**RETRY_CONFIG)
    async def get_roles(self, raise_on_err: bool = False) -> RoleList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting roles failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleList(**res.json())

    @retry(**RETRY_CONFIG)
    async def get_groups_with_role(self, role_id: int, raise_on_err: bool = False) -> RoleGroupList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting roles failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleGroupList(**res.json())

    @retry(**RETRY_CONFIG)
    async def assign_groups_to_role(self, role_id: int, groups: GroupIds, raise_on_err: bool = False) -> RoleGroupList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'
        
        payload = groups.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.post(api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Assigning role failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleGroupList(**res.json())
        

    @retry(**RETRY_CONFIG)
    async def remove_groups_from_role(self, role_id: int, groups: GroupIds, raise_on_err: bool = False) -> RoleGroupList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/groups'
        
        payload = groups.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Assigning role failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleGroupList(**res.json())
            
    @retry(**RETRY_CONFIG)
    async def get_users_with_role(self, role_id: int, raise_on_err: bool = False) -> RoleUserList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting roles failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleUserList(**res.json())

    @retry(**RETRY_CONFIG)
    async def assign_users_to_role(self, role_id: int, users: UserIds, raise_on_err: bool = False) -> RoleUserList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'
        
        payload = users.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.post(api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Assigning role failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleUserList(**res.json())

    @retry(**RETRY_CONFIG)
    async def remove_users_from_role(self, role_id: int, users: UserIds, raise_on_err: bool = False) -> RoleUserList:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/' + str(role_id) + '/users'
        
        payload = users.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Assigning role failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        return RoleUserList(**res.json())
    
    def make_user_group_ids(self, ids: List[int], is_user: bool = True):
        
        payload = {
            "ids": ids
        }
        
        if is_user:
            return UserIds(**payload)
        else:
            return GroupIds(**payload)
    