"""
Async DRACOON eventlog adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/eventlog

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""

from typing import List
import httpx
import logging
from pydantic import validate_arguments
import urllib.parse

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.errors import ClientDisconnectedError, InvalidClientError
from .responses import AuditNodeInfoResponse, AuditNodeResponse, LogEventList


class DRACOONEvents:

    """
    API wrapper for DRACOON eventlog endpoint:
    Events and permissions audit management - requires user auditor role.
    Please note: using the eventlog API for events is discouraged. Please 
    use the reports API wrapper instead.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.eventlog')
        
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/eventlog'
    
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

            self.logger.debug("DRACOON eventlog adapter created.")
        
        else:
            self.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
   
    @validate_arguments
    async def get_permissions(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err = False) -> List[AuditNodeResponse]:
        """ get permissions for all nodes (rooms) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/audits/nodes/?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting permissions failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node permission audit.")
        tmp_list = res.json()
        
        return [AuditNodeResponse(**node_info) for node_info in tmp_list]
    
    @validate_arguments
    async def get_rooms(self, parent_id: int = 0, offset: int = 0, filter: str = None, 
                                   limit: int = None, sort: str = None, raise_on_err = False) -> AuditNodeInfoResponse:
        """ get permissions for all nodes (rooms) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/audits/node_info/?parent_id={str(parent_id)}&offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting permissions failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node permission audit.")
        return AuditNodeInfoResponse(**res.json())

    @validate_arguments
    async def get_events(self, offset: int = 0, filter: str = None, limit: int = None, 
                        sort: str = None, date_start: str = None, date_end: str = None, operation_id: int = None, user_id: int = None, raise_on_err = False) -> LogEventList:
        """ get events (audit log) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
        
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/events/?offset={offset}'
        if date_start != None: api_url += f'&date_start={date_start}'
        if date_end != None: api_url += f'&date_end={date_end}'
        if operation_id != None: api_url += f'&type={str(operation_id)}'
        if user_id != None: api_url += f'&user_id={str(user_id)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)

        except httpx.HTTPStatusError as e:
            self.logger.error("Getting event log failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Retrieved events from eventlog.")
        return LogEventList(**res.json())


