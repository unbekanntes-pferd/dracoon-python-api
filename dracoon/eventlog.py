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

from pydantic import validate_arguments

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
