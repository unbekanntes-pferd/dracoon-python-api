# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for shares / file requests
# Requires Dracoon call handlers 
# Version 0.1.0
# Author: Octavio Simone, 30.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

# collection of DRACOON API calls for shares & file requests
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

from typing import List
from pydantic import validate_arguments
from .shares_models import CreateFileRequest, CreateShare, SendShare, UpdateFileRequest, UpdateFileRequests, UpdateShare, UpdateShares

# get list of all (download) shares
@validate_arguments
def get_shares(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/shares/downloads?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a new (download) share - for model see documentation linked above
@validate_arguments
def create_share(params: CreateShare):
    api_call = {
        'url': '/shares/downloads',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# delete an array of shares
@validate_arguments
def delete_shares(shareIDs: List[int]):
    api_call = {
        'url': '/shares/downloads',
        'body': {
            "shareIds": shareIDs
        },
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get information about a specific share (given share ID)
@validate_arguments
def get_share(shareID: int):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update a list of shares (given share IDs)
@validate_arguments
def update_shares(params: UpdateShares):
    api_call = {
        'url': '/shares/downloads',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# update a specific share (given share ID)
@validate_arguments
def update_share(shareID: int, params: UpdateShare):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete specific share (given share ID)
@validate_arguments
def delete_share(shareID: int):
    api_call = {
        'url': '/shares/downloads/' + str(shareID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# send share via email 
@validate_arguments
def send_share(shareID: int, params):
    api_call = {
        'url': '/shares/downloads/' + str(shareID) + '/email',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call


# get list of all (download) shares
@validate_arguments
def get_file_requests(offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/shares/uploads?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None: api_call["url"] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
    
    return api_call

# create a new file request - for model see documentation linked above
@validate_arguments
def create_file_request(params: CreateFileRequest):
    api_call = {
        'url': '/shares/uploads',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# delete an array of file requests
@validate_arguments
def delete_file_requests(requestIDs: List[int]):
    api_call = {
        'url': '/shares/uploads',
        'body': {
            "shareIds": requestIDs
        },
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get information about a specific file request (given request ID)
@validate_arguments
def get_file_request(requestID: int):
    api_call = {
        'url': '/shares/uploads/' + str(requestID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# update a specific file request (given request ID)
@validate_arguments
def update_file_request(params: UpdateFileRequests):
    api_call = {
        'url': '/shares/uploads',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call


# update a specific file request (given request ID)
@validate_arguments
def update_file_request(shareID: int, params: UpdateFileRequest):
    api_call = {
        'url': '/shares/uploads/' + str(shareID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete specific file request (given request ID)
@validate_arguments
def delete_file_request(requestID: int):
    api_call = {
        'url': '/shares/uploads/' + str(requestID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# send file request via email 
@validate_arguments
def send_file_request(shareID: int, params: SendShare):
    api_call = {
        'url': '/shares/uploads/' + str(shareID) + '/email',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call









