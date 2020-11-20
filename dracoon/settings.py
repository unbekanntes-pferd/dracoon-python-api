# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for settings
# Requires Dracoon call handlers
# Version 0.1.0
# Author: Octavio Simone, 04.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


# collection of DRACOON API calls for settings (Webhooks)
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/groups
# Webhooks documentation: https://support.dracoon.com/hc/de/articles/360013167959-Webhooks 
# Please note: maximum 500 items are returned in GET requests
# - refer to documentation for details on filtering and offset
# - use documentation for payload description
# All requests with bodies use generic params variable to pass JSON body

# get customer settings
def get_settings():
    api_call = {
            'url': '/settings',
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    return api_call

# get customer settings
def update_settings(params):
    api_call = {
            'url': '/settings',
            'body': params,
            'method': 'PUT',
            'Content-Type': 'application/json'
        }
    return api_call

# get customer webhooks 
def get_webhooks(offset=0, filter=None, limit=None, sort=None):
    api_call = {
            'url': '/settings/webhooks?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
        
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# create a webhook with given parameters - please refer to documentation above
def create_webhook(params):
    api_call = {
        'url': '/settings/webhooks',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# get webhook details for given hook id
def get_webhook(hookID):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# update webhook data for given hook id
def update_webhook(hookID, params):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete webhook for given hook id
def delete_webhook(hookID, params):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get webhook event types
def get_hook_event_types():
    api_call = {
            'url': '/settings/webhooks/event_types',
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    return api_call