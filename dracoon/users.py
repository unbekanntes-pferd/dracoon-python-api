# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for user management
# Requires Dracoon call handlers 
# Version 0.1.0
# Author: Octavio Simone, 04.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

# collection of DRACOON API calls for user management
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/users
# Please note: maximum 500 items are returned in GET requests 
# - refer to documentation for details on filtering and offset 
# - use documentation for payload description 
# All requests with bodies use generic params variable to pass JSON body

from pydantic import validate_arguments
from .users_models import CreateUser, SetUserAttributes, UpdateUser, UpdateUserAttributes

# get all users
@validate_arguments
def get_users(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# create a user with given parameters
@validate_arguments
def create_user(params: CreateUser):
    api_call = {
        'url': '/users',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get user details for given user id
@validate_arguments
def get_user(userID: int):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update user's meta data for given user id
@validate_arguments
def update_user(userID: int, params: UpdateUser):
    api_call = {
        'url': '/users/' + str(userID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete user for given user id
@validate_arguments
def delete_user(userID: int):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get user details for given user id
@validate_arguments
def get_user_groups(userID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users/' + str(userID) + '/groups?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# get rooms in which user is last remaining admin (prevents user deletion!)
@validate_arguments
def get_user_last_admin_rooms(userID: int):
    api_call = {
        'url': '/users/' + str(userID) + '/last_admin_rooms',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get roles assigned to user
@validate_arguments
def get_user_roles(userID: int):
    api_call = {
        'url': '/users/' + str(userID) + '/roles',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get custom user attributes (key, value)
@validate_arguments
def get_user_attributes(userID: int, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# set custom user attributes (key, value)
@validate_arguments
def set_user_attributes(userID: int, params: SetUserAttributes):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call


# update custom user attributes (key, value)
@validate_arguments
def update_user_attributes(userID: int, params: UpdateUserAttributes):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call




    








    
        