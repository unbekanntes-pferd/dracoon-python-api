"""
Async DRACOON reports adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for report management
Documentation: https://staging.dracoon.com/reporting/api (current beta – API on dracoon.team tbd)
Please note: maximum 500 items are returned in GET requests
 - refer to documentation for details on filtering and offset
 - use documentation for payload description

"""

from typing import List
import httpx

from .core import DRACOONClient, OAuth2ConnectionType
from .reports_models import CreateReport
from .core_models import ApiDestination
from pydantic import validate_arguments

class DRACOONReports:

    def __init__(self, dracoon_client: DRACOONClient):

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.reporting_base_url + '/reports'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_report(self, report: CreateReport):

        payload = report.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res
    
    @validate_arguments
    async def get_reports(self, name: str, type: str = None, sub_type: str = None, state: str = None, 
                has_error: bool = None, enabled: bool = None, 
                offset: int = 0, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/?offset={offset}'
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 
        if type != None: api_url += f'&type={type}' 
        if sub_type != None: api_url += f'&subType={sub_type}'
        if enabled != None: api_url += f'&type={str(enabled).lower()}' 
        if has_error != None: api_url += f'&hasError={str(has_error).lower()}'
        if state != None: api_url += f'&state={state}'

        try:
            res = await self.dracoon.http.get(self.api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res


"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# get reports
@validate_arguments
def get_reports(name: str, type: str = None, sub_type: str = None, state: str = None, 
                has_error: bool = None, enabled: bool = None, 
                offset: int = 0, limit: int = None, sort: str = None):
    api_call = {
            'url': '/reports?offset=' + str(offset), 
            'body': None,
            'method': 'GET',
            'content_type': 'application/json',
            'destination': ApiDestination.Reporting
        }

    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    if type != None: api_call['url'] += '&type=' + type
    if sub_type != None: api_call['url'] += '&subType=' + sub_type
    if enabled != None: api_call['url'] += '&type=' + str(enabled).lower()
    if has_error != None: api_call['url'] += '&hasError=' + str(has_error).lower()
    if state != None: api_call['url'] += '&state=' + state

    return api_call

# create a report
@validate_arguments
def create_report(params: CreateReport):

    api_call = {
            'url': '/reports', 
            'body': params,
            'method': 'POST',
            'content_type': 'application/json',
            'destination': ApiDestination.Reporting
        }

    return api_call








