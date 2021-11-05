# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for system events log
# Requires Dracoon call handlers
# Version 0.1.0
# Author: Octavio Simone, 10.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


# collection of DRACOON API calls for system events log
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/eventlog
# Please note: maximum 500 items are returned in GET requests
# - refer to documentation for details on filtering and offset
# Important: role log auditor required (!)

import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType

class DRACOONEvents:

    def __init__(self, dracoon_client: DRACOONClient):

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/eventlog'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')
   
    @validate_arguments
    async def get_permissions(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

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

