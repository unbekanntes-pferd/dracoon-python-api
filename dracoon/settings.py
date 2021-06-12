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

from pydantic import validate_arguments
from .settings_models import CreateWebhook, UpdateSettings, UpdateWebhook

# get customer settings
def get_settings():
    api_call = {
            'url': '/settings',
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    return api_call

# get customer settings
@validate_arguments
def update_settings(params: UpdateSettings):
    api_call = {
            'url': '/settings',
            'body': params,
            'method': 'PUT',
            'content_type': 'application/json'
        }
    return api_call

# get customer webhooks 
@validate_arguments
def get_webhooks(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/settings/webhooks?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
        
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# create a webhook with given parameters - please refer to documentation above
@validate_arguments
def create_webhook(params: CreateWebhook):
    api_call = {
        'url': '/settings/webhooks',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get webhook details for given hook id
@validate_arguments
def get_webhook(hookID: int):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update webhook data for given hook id
@validate_arguments
def update_webhook(hookID: int, params: UpdateWebhook):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete webhook for given hook id
@validate_arguments
def delete_webhook(hookID: int):
    api_call = {
        'url': '/settings/webhooks/' + str(hookID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get webhook event types
def get_hook_event_types():
    api_call = {
            'url': '/settings/webhooks/event_types',
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    return api_call