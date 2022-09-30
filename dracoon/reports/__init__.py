"""
Async DRACOON reports adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for report management
Documentation: https://staging.dracoon.com/reporting/api (current beta – API on dracoon.team tbd)
Please note: maximum 500 items are returned in GET requests
 - refer to documentation for details on filtering and offset
 - use documentation for payload description

"""


from typing import List
import httpx
import logging
from pydantic import validate_arguments
from datetime import datetime


from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.errors import ClientDisconnectedError, InvalidClientError
from .models import CreateReport, ReportFilter, ReportFormat, ReportSubType, ReportType
from .responses import ReportList


class DRACOONReports:

    """
    API wrapper for DRACOON reports API:
    Reports management - requires auditor role.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client')
        
        self.logger = logging.getLogger('dracoon.reports')
        
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.reporting_base_url + '/reports'
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
            self.logger.debug("DRACOON reports adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def create_report(self, report: CreateReport, raise_on_err: bool = False) -> None:
        """ create a new report """
        payload = report.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        try:
            res = await self.dracoon.http.post(self.api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating report failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Created report.")
        return None
    
    def make_report(self, name: str, target_id: int, formats: List[ReportFormat], type: ReportType = ReportType.single, 
                    sub_type: ReportSubType = ReportSubType.audit_report, 
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

        return CreateReport(**report)


    def make_report_filter(self, from_date: datetime = None, to_date: datetime = None, parent_room_id: int = None, 
                           user_id: int = None, operations: List[int] = None) -> ReportFilter:
        """ make an optional report filter needed for make_report() """

        filter = {}

        if from_date: filter["fromDate"] = from_date
        if to_date: filter["toDate"] = to_date
        if parent_room_id: filter["parentRoom"] = parent_room_id
        if user_id: filter["userId"] = user_id
        if operations: filter["operations"] = operations

        return ReportFilter(**filter)
    
    @validate_arguments
    async def get_reports(self, name: str = None, type: str = None, sub_type: str = None, state: str = None, 
                has_error: bool = None, enabled: bool = None, 
                offset: int = 0, limit: int = None, sort: str = None, raise_on_err: bool = False) -> ReportList:
        """ list (all) reports """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

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

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting reports failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved reports.")
        return ReportList(**res.json())

    @validate_arguments
    async def delete_reports(self, report_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of reports (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "ids": report_list
        }
        
        try:
            res = await self.dracoon.http.request(method='DELETE', url=self.api_url, json=payload, headers=self.dracoon.http.headers)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting reports failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Deleted reports.")
        return None

    @validate_arguments
    async def delete_report(self, report_id: int, raise_on_err: bool = False) -> None:
        """ delete a specific report (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(report_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting report failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted report.")
        return None