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

def get_users(offset=0, filter=None, sort=None, limit=None):
    api_call = {
        'url': '/users?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# create a user with given parameters 
def create_user(params):
    api_call = {
        'url': '/users',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# get user details for given user id
def get_user(userID):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# update user's meta data for given user id
def update_user(userID, params):
    api_call = {
        'url': '/users/' + str(userID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete user for given user id
def delete_user(userID, params):
    api_call = {
        'url': '/users/' + str(userID),
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get user details for given user id
def get_user_groups(userID, offset=0, filter=None, limit=None, sort=None):
    api_call = {
        'url': '/users/' + str(userID) + '/groups?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# get rooms in which user is last remaining admin (prevents user deletion!)
def get_user_last_admin_rooms(userID):
    api_call = {
        'url': '/users/' + str(userID) + '/last_admin_rooms',
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# get roles assigned to user
def get_user_roles(userID):
    api_call = {
        'url': '/users/' + str(userID) + '/roles',
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# get custom user attributes (key, value)
def get_user_attributes(userID, offset=0, filter=None, limit=None, sort=None):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# set custom user attributes (key, value)
def set_user_attributes(userID, params):
    api_call = {
        'url': '/users/' + str(userID) + '/userAttributes',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call



    








    
        