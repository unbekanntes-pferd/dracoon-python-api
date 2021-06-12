# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for user account information
# Requires Dracoon call handlers 
# Version 0.1.0
# Author: Octavio Simone, 13.05.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

# collection of DRACOON API calls for user management
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/user
# Please note: maximum 500 items are returned in GET requests 
# - refer to documentation for details on filtering and offset 
# - use documentation for payload description 
# All requests with bodies use generic params variable to pass JSON body


from pydantic import validate_arguments
from .user_models import UpdateAccount
from .crypto_models import UserKeyPairContainer, UserKeyPairVersion

# get account information for current user
@validate_arguments
def get_account_information(more_info: bool = False):

    api_call = {
        'url': '/user/account?more_info=' + str(more_info).lower(),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    return api_call

# update account information for current user
@validate_arguments
def update_account_information(params: UpdateAccount):

    api_call = {
        'url': '/user/account',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    
    return api_call

# get user keypair (encrypted)
@validate_arguments
def get_user_keypair(version: UserKeyPairVersion = None):

    api_call = {
        'url': '/user/account/keypair',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if version != None: api_call["url"] += '?version=' + version.value

    return api_call

# set user keypair 
@validate_arguments
def set_user_keypair(params: UserKeyPairContainer):

    api_call = {
        'url': '/user/account/keypair',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }

    return api_call

# delete user keypair 
@validate_arguments
def delete_user_keypair(version: UserKeyPairVersion = None):

    api_call = {
        'url': '/user/account/keypair',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }

    if version != None: api_call["url"] += '?version=' + version.value


    return api_call


