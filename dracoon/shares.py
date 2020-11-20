# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for shares / file requests
# Requires Dracoon call handlers 
# Version 0.1.0
# Author: Octavio Simone, 30.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#



# collection of DRACOON API calls for shares & file requests
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

# get list of all (download) shares
def get_shares(offset=0, filter=None, limit=None, sort=None):
    api_call = {
        'url': '/shares/downloads?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a new (download) share - for model see documentation linked above
def create_share(params):
    api_call = {
        'url': '/shares/downloads',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# delete an array of shares
def delete_shares(shareIDs):
    api_call = {
        'url': '/shares/downloads',
        'body': {
            "shareIds": shareIDs
        },
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get information about a specific share (given share ID)
def get_share(shareID):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# update a specific share (given share ID)
def update_share(shareID, params):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete specific share (given share ID)
def delete_share(shareID):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# send share via email 
def send_share(shareID, params):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call


# get list of all (download) shares
def get_file_requests(offset=0, filter=None, limit=None, sort=None):
    api_call = {
        'url': '/shares/uploads?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a new file request - for model see documentation linked above
def create_file_request(params):
    api_call = {
        'url': '/shares/uploads',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# delete an array of file requests
def delete_file_requests(requestIDs):
    api_call = {
        'url': '/shares/uploads',
        'body': {
            "shareIds": requestIDs
        },
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get information about a specific file request (given request ID)
def get_file_request(requestID):
    api_call = {
        'url': '/shares/uploads/' + str(requestID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# update a specific file request (given request ID)
def update_file_request(shareID, params):
    api_call = {
        'url': '/shares/uploads/' + str(shareID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete specific file request (given request ID)
def delete_file_request(requestID):
    api_call = {
        'url': '/shares/uploads/' + str(requestID),
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# send file request via email 
def send_file_request(shareID, params):
    api_call = {
        'url': '/shares/uploads/' + str(shareID) + 'email',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call









