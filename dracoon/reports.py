# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for report management
# Requires Dracoon call handlers
# Version 0.1.0
# Author: Octavio Simone, 13.08.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


# collection of DRACOON API calls for report management
# documentation: https://staging.dracoon.com/reporting/api (current beta – API on dracoon.team tbd)
# Please note: maximum 500 items are returned in GET requests
# - refer to documentation for details on filtering and offset
# - use documentation for payload description
# All requests with bodies use generic params variable to pass JSON body

from typing import List
from .reports_models import CreateReport
from .core_models import ApiDestination
from pydantic import validate_arguments

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

