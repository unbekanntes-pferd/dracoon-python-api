"""
Async DRACOON shares adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

"""

from typing import List
import httpx
from pydantic import validate_arguments

from dracoon.core import DRACOONClient, OAuth2ConnectionType
from .shares_models import CreateFileRequest, CreateShare, SendShare, UpdateFileRequest, UpdateFileRequests, UpdateShare, UpdateShares

class DRACOONShares:

    def __init__(self, dracoon_client: DRACOONClient):

        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/shares'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')


    # get list of all (download) shares
    @validate_arguments
    async def get_shares(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # create a new (download) share - for model see documentation linked above
    @validate_arguments
    async def create_share(self, share: CreateShare):

        payload = share.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete an array of shares
    @validate_arguments
    async def delete_shares(self, share_list: List[int]):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "shareIds": share_list
        }
        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get information about a specific share (given share ID)
    @validate_arguments
    async def get_share(self, share_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update a list of shares (given share IDs)
    @validate_arguments
    async def update_shares(self, shares_update: UpdateShares):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads'

        payload = shares_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update a specific share (given share ID)
    @validate_arguments
    async def update_share(self, share_id: int, share_update: UpdateShare):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        payload = share_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete specific share (given share ID)
    @validate_arguments
    async def delete_share(self, share_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # send share via email 
    @validate_arguments
    async def mail_share(self, share_id: int, send_share: SendShare):
    
        payload = send_share.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res


    # get list of all (download) shares
    @validate_arguments
    async def get_file_requests(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # create a new file request - for model see documentation linked above
    @validate_arguments
    async def create_file_request(self, file_request: CreateFileRequest):

        payload = file_request.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete an array of file requests
    @validate_arguments
    async def delete_file_requests(self, file_request_list: List[int]):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "shareIds": file_request_list
        }
        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get information about a specific file request (given request ID)
    @validate_arguments
    async def get_file_request(self, file_request_id: int):
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update a specific file request (given request ID)
    @validate_arguments
    async def update_file_requests(self, file_requests_update: UpdateFileRequests):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads'

        payload = file_requests_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update a specific file request (given request ID)
    @validate_arguments
    async def update_file_request(self, file_request_id: int, file_request_update: UpdateFileRequest):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        payload = file_request_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete specific file request (given request ID)
    @validate_arguments
    async def delete_file_request(self, file_request_id: int):

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res

    # send file request via email 
    @validate_arguments
    async def mail_file_request(self, file_request_id: int, send_file_request: SendShare):

        payload = send_file_request.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        return res




"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

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