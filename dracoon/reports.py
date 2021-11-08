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

from re import sub
from typing import List
import httpx

from .core import DRACOONClient, OAuth2ConnectionType
from .reports_models import CreateReport, ReportFilter, ReportFormat, ReportSubType, ReportType
from .core_models import ApiDestination
from pydantic import validate_arguments
from datetime import datetime

class DRACOONReports:

    """
    API wrapper for DRACOON reports API:
    Reports management - requires auditor role.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.reporting_base_url + '/reports'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_report(self, report: CreateReport):
        """ create a new report """
        payload = report.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res
    
    def make_report(self, name: str, target_id: int, formats: List[ReportFormat], type: ReportType = ReportType.single, sub_type: ReportSubType = ReportSubType.audit_report, 
                    enabled: bool = None, filter: ReportFilter = None) -> CreateReport:
        """ make a report payload to generate a report """
        report = {
            "name": name,
            "target": {
                "id": target_id
            },
            "type": type,
            "subType": sub_type,
            "formats": formats  
        }

        if enabled is not None: report["enabled"] = enabled
        if filter: report["filter"] = filter


    def make_report_filter(self, from_date: datetime = None, to_date: datetime = None, parent_room_id: int = None, user_id: int = None, operations: List[int] = None) -> ReportFilter:
        """ make an optional report filter needed for make_report() """

        filter = {}

        if from_date: filter["fromDate"] = from_date
        if to_date: filter["toDate"] = to_date
        if parent_room_id: filter["parentRoom"] = parent_room_id
        if user_id: filter["userId"] = user_id
        if operations: filter["operations"] = operations

        return filter
    
    @validate_arguments
    async def get_reports(self, name: str = None, type: str = None, sub_type: str = None, state: str = None, 
                has_error: bool = None, enabled: bool = None, 
                offset: int = 0, limit: int = None, sort: str = None):
        """ list (all) reports """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/?offset={offset}'
        if name: api_url += f'&name={name}' 
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

    @validate_arguments
    async def delete_reports(self, report_list: List[int]):
        """ delete a list of reports (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "ids": report_list
        }
        
        try:
            res = await self.dracoon.http.request(method='DELETE', url=self.api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    @validate_arguments
    async def delete_report(self, report_id: int):
        """ delete a specific report (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(report_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

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








