"""
Async DRACOON eventlog adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for user management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/eventlog

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""

import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType

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
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/eventlog'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')
   
    @validate_arguments
    async def get_permissions(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
        """ get permissions for all nodes (rooms) """
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

    @validate_arguments
    async def get_events(self, offset: int = 0, filter: str = None, limit: int = None, 
                        sort: str = None, date_start: str = None, date_end: str = None, operation_id: int = None, user_id: int = None):
        """ get events (audit log) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/?offset={offset}'
        if date_start != None: api_url += f'&date_start={date_start}'
        if date_end != None: api_url += f'&date_end={date_end}'
        if operation_id != None: api_url += f'&type={str(operation_id)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res


"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# get assigned users per node
@validate_arguments
def get_user_permissions(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/eventlog/audits/nodes?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }

    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

@validate_arguments
def get_events(offset: int = 0, dateStart: str = None, dateEnd: str = None, operationID: int = None, userID: int = None, limit: int = None, sort: int = None):
    api_call = {
            'url': '/eventlog/events/' + '?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }

    if dateStart != None: api_call['url'] += '&date_start=' + dateStart
    if dateEnd != None: api_call['url'] += '&date_end=' + dateEnd
    if operationID != None: api_call['url'] += '&type=' + str(operationID)
    if userID != None: api_call['url'] += '&user_id=' + str(userID)
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

