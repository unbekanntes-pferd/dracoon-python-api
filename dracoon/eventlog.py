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

# get assigned users per node
def get_user_permissions(offset=0, filter=None):
    if filter == None:
        api_call = {
            'url': '/eventlog/audits/nodes?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    else:
        api_call = {
            'url': '/eventlog/audits/nodes?offset=' + str(offset) + '&filter=' + filter,
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    return api_call


def get_events(dateStart=None, dateEnd=None, operationID=None, userID=None, offset=0):
    api_call = {
            'url': '/eventlog/events/' + '?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }

    if dateStart != None: api_call['url'] += '&date_start=' + dateStart
    if dateEnd != None: api_call['url'] += '&date_end=' + dateEnd
    if operationID != None: api_call['url'] += '&type=' + str(operationID)
    if userID != None: api_call['url'] += '&user_id=' + str(userID)

    return api_call