# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for group management
# Requires Dracoon call handlers
# Version 0.1.0
# Author: Octavio Simone, 04.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


# collection of DRACOON API calls for group management
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/groups
# Please note: maximum 500 items are returned in GET requests
# - refer to documentation for details on filtering and offset
# - use documentation for payload description
# All requests with bodies use generic params variable to pass JSON body

from typing import List
from pydantic import validate_arguments
from .groups_models import CreateGroup, UpdateGroup

# get list of groups
@validate_arguments
def get_groups(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/groups?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a group with given parameters
@validate_arguments
def create_group(params: CreateGroup):
    api_call = {
        'url': '/groups',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }

    return api_call

# get group details for given group id
@validate_arguments
def get_user(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update group's meta data for given group id
@validate_arguments
def update_group(groupID: int, params: UpdateGroup):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete user for given user id
@validate_arguments
def delete_group(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get rooms in which group is last remaining admin (prevents user deletion!)
@validate_arguments
def get_group_last_admin_rooms(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/last_admin_rooms',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get roles assigned to group
@validate_arguments
def get_group_roles(groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/roles',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get group users
@validate_arguments
def get_group_users(groupID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
            'url': '/groups/' + str(groupID) + '/users?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'content_type': 'application/json'
        }
    
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# update assigned users (array of user ids) to a group with given group id
@validate_arguments
def update_group_users(userIDs: List[int], groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/users',
        'body': {
            "ids": userIDs
        },
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# delete assigned users (array of user ids) from a group with given group id
@validate_arguments
def delete_group_users(userIDs: List[int], groupID: int):
    api_call = {
        'url': '/groups/' + str(groupID) + '/users',
        'body': {
            "ids": userIDs
        },
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call
