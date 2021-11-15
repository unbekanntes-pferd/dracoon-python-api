"""
Async DRACOON shares adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

"""

from typing import List
import httpx
from pydantic import validate_arguments

from .core import DRACOONClient, OAuth2ConnectionType
from .crypto_models import FileKey, UserKeyPairContainer
from .shares_models import CreateFileRequest, CreateShare, Expiration, SendShare, UpdateFileRequest, UpdateFileRequests, UpdateShare, UpdateShares
from .shares_responses import DownloadShare, DownloadShareList, UploadShare, UploadShareList

class DRACOONShares:

    """
    API wrapper for DRACOON shares endpoint:
    Share and file request management - requires manage shares or file request permissions.
    """


    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
           self.dracoon = dracoon_client
           self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/shares'
        else:
            raise ValueError('DRACOON client must be connected: client.connect()')

    # get list of all (download) shares
    @validate_arguments
    async def get_shares(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None) -> DownloadShareList:
        """ list (all) shares visible as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting shares in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return DownloadShareList(**res.json())

    # create a new (download) share - for model see documentation linked above
    @validate_arguments
    async def create_share(self, share: CreateShare) -> DownloadShare:
        """ create a new share """
        payload = share.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Creating share in DRACOON failed: {e.response.status_code} ({e.request.url})')


        return DownloadShare(**res.json())

    def make_share(self, node_id: int, name: str = None, password: str = None, expiration: str = None, notes: str = None, internal_notes: str = None, 
                   show_creator: bool = None, show_creator_login: bool = None, max_downloads: int = None, keypair: UserKeyPairContainer = None, file_key: FileKey = None, 
                   language: str = None, sms_recipients: List[str] = None) -> CreateShare:
        
        """ make a share payload required for create_share() """
        share = {
            "nodeId": node_id
        }

        if name: share["name"] = name
        if password: share["password"] = password
        if expiration: share["expiration"] = expiration
        if notes: share["notes"] = notes
        if internal_notes: share["internalNotes"] = internal_notes
        if show_creator is not None: share["showCreatorName"] = show_creator
        if max_downloads: share["maxDownloads"] = max_downloads
        if keypair: share["keyPair"] = keypair
        if file_key: share["fileKey"] = file_key
        if language: share["langauge"] = file_key
        if sms_recipients: share["textMessageRecipients"] = sms_recipients

        return CreateShare(**share)

    # delete an array of shares
    @validate_arguments
    async def delete_shares(self, share_list: List[int]) -> None:
        """ delete a list of shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "shareIds": share_list
        }
        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting shares in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # get information about a specific share (given share ID)
    @validate_arguments
    async def get_share(self, share_id: int) -> DownloadShare:
        """ get information of a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting share {share_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return DownloadShare(**res.json())

    # update a list of shares (given share IDs)
    @validate_arguments
    async def update_shares(self, shares_update: UpdateShares) -> None:
        """ bulk update specific shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads'

        payload = shares_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating shares in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None
    
    def make_shares_update(self, shares_list = List[int], expiration: Expiration = None, 
                          show_creator_name: bool = None, show_creator_login: bool = None, 
                          max_downloads: int = None, reset_max_downloads: bool = True) -> UpdateShares:

        """ make a shares update payload required for update_shares() """
        shares_update = {

            "objetIds": shares_list

            }

        if expiration: shares_update["expiration"] = expiration
        if show_creator_login is not None: shares_update["showCreatorUsername"] = show_creator_login
        if show_creator_name is not None: shares_update["showCreatorName"] = show_creator_name
        if max_downloads: shares_update["maxDownloads"] = max_downloads
        if reset_max_downloads is not None: shares_update["resetMaxDownloads"] = reset_max_downloads
    
        return UpdateShares(**shares_update)

    def make_share_update(self, name: str = None, password: str = None, expiration: str = None, notes: str = None, internal_notes: str = None, 
                   show_creator: bool = None, show_creator_login: bool = None, max_downloads: int = None, keypair: UserKeyPairContainer = None, file_key: FileKey = None, 
                   language: str = None, sms_recipients: List[str] = None, default_country: str = None,
                   reset_max_downloads: bool = None, reset_password: bool = None) -> UpdateShare:
        
        """ make a share update payload required for update_share() """
        share_update = {}

        if name: share_update["name"] = name
        if password: share_update["password"] = password
        if expiration: share_update["expiration"] = expiration
        if notes: share_update["notes"] = notes
        if internal_notes: share_update["internalNotes"] = internal_notes
        if show_creator is not None: share_update["showCreatorName"] = show_creator
        if show_creator_login is not None: share_update["showCreatorUsername"] = show_creator_login
        if max_downloads: share_update["maxDownloads"] = max_downloads
        if keypair: share_update["keyPair"] = keypair
        if file_key: share_update["fileKey"] = file_key
        if language: share_update["receiverLangauge"] = language
        if default_country: share_update["defaultCountry"] = default_country
        if sms_recipients: share_update["textMessageRecipients"] = sms_recipients
        if reset_max_downloads is not None: share_update["resetMaxDownloads"] = reset_max_downloads
        if reset_password is not None: share_update["resetPassword"] = reset_password

        return UpdateShare(**share_update)



    @validate_arguments
    async def update_share(self, share_id: int, share_update: UpdateShare) -> DownloadShare:
        """ update a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        payload = share_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating share {share_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')


        return DownloadShare(**res.json())

    # delete specific share (given share ID)
    @validate_arguments
    async def delete_share(self, share_id: int) -> None:
        """ delete a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting share {share_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # send share via email 
    @validate_arguments
    async def mail_share(self, share_id: int, send_share: SendShare) -> None:
        """ send a specific share via email (by id) """
        payload = send_share.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/downloads/{str(share_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Sending share {share_id} to {send_share.recipients} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None


    # get list of all (download) shares
    @validate_arguments
    async def get_file_requests(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None) -> UploadShareList:
        """ list all file requests visible as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
          
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting file requests in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UploadShareList(**res.json())

    # create a new file request - for model see documentation linked above
    @validate_arguments
    async def create_file_request(self, file_request: CreateFileRequest) -> UploadShare:
        """ create a new file request """
        payload = file_request.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Creating file request in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UploadShare(**res.json())

    def make_file_request(self, target_id: int, name: str = None, password: str = None, expiration: str = None, file_expiration: int = None, notes: str = None, internal_notes: str = None, 
                   show_creator: bool = None, show_creator_login: bool = None, max_slots: int = None, max_size: int = None, show_uploaded_files: bool = None,
                   language: str = None, sms_recipients: List[str] = None) -> CreateFileRequest:  
        """ make a share payload required for create_file_request() """
        file_request = {
            "targetId": target_id
        }

        if name: file_request["name"] = name
        if password: file_request["password"] = password
        if expiration: file_request["expiration"] = expiration
        if file_expiration: file_request["fileExpiryPeriod"] = file_expiration
        if notes: file_request["notes"] = notes
        if internal_notes: file_request["internalNotes"] = internal_notes
        if show_creator is not None: file_request["showCreatorName"] = show_creator
        if show_creator_login is not None: file_request["showCreatorUsername"] = show_creator_login
        if max_slots: file_request["maxSlots"] = max_slots
        if max_size: file_request["maxSize"] = max_size
        if language: file_request["receiverLangauge"] = language
        if show_uploaded_files is not None: file_request["showUploadedFiles"] = show_uploaded_files
        if sms_recipients: file_request["textMessageRecipients"] = sms_recipients

        return CreateFileRequest(**file_request)

    # delete an array of file requests
    @validate_arguments
    async def delete_file_requests(self, file_request_list: List[int]) -> None:
        """ delete a list of shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "shareIds": file_request_list
        }
        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting file requests in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # get information about a specific file request (given request ID)
    @validate_arguments
    async def get_file_request(self, file_request_id: int) -> UploadShare:
        """ get information of a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Getting file request {file_request_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UploadShare(**res.json())

    # update a specific file request (given request ID)
    @validate_arguments
    async def update_file_requests(self, file_requests_update: UpdateFileRequests) -> None:
        """ bulk update specifics file requests (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads'

        payload = file_requests_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating file requests in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    def make_file_requests_update(self, file_requests_list = List[int], expiration: Expiration = None, file_expiration: int = None,
                          show_creator_name: bool = None, show_creator_login: bool = None, 
                          max_slots: int = None, max_size: int = None, show_uploaded_files: bool = None, reset_max_size: bool = True, 
                          reset_max_slots: bool = None, reset_file_expiration: bool = None) -> UpdateFileRequests:

        """ make a file_requests update payload required for update_file_requests() """
        file_requests_update = {

            "objetIds": file_requests_list

            }

        if expiration: file_requests_update["expiration"] = expiration
        if file_expiration: file_requests_update["filesExpiryPeriod"] = file_expiration
        if reset_file_expiration is not None: file_requests_update["resetFilesExpiryPeriod"] = reset_file_expiration
        if show_creator_login is not None: file_requests_update["showCreatorUsername"] = show_creator_login
        if show_creator_name is not None: file_requests_update["showCreatorName"] = show_creator_name
        if max_slots: file_requests_update["maxSlots"] = max_slots
        if max_size: file_requests_update["maxSize"] = max_size
        if reset_max_slots is not None: file_requests_update["resetSlots"] = reset_max_slots
        if reset_max_size is not None: file_requests_update["resetSize"] = reset_max_size
        if show_uploaded_files is not None: file_requests_update["showUploadedFiles"] = show_uploaded_files

        return UpdateFileRequests(**file_requests_update)

    def make_file_request_update(self, name: str = None, password: str = None, expiration: str = None, file_expiration: int = None, notes: str = None, internal_notes: str = None, 
                   show_creator: bool = None, show_creator_login: bool = None, max_slots: int = None, max_size: int = None, show_uploaded_files: bool = None,
                   language: str = None, sms_recipients: List[str] = None, reset_max_slots: bool = None, reset_max_size: bool = None,
                   reset_file_expiration: bool = None) -> UpdateFileRequest:  
        """ make a share payload required for create_file_request() """
        file_request = { }

        if name: file_request["name"] = name
        if password: file_request["password"] = password
        if expiration: file_request["expiration"] = expiration
        if file_expiration: file_request["filesExpiryPeriod"] = file_expiration
        if reset_file_expiration is not None: file_request["resetFilesExpiryPeriod"] = reset_file_expiration
        if notes: file_request["notes"] = notes
        if internal_notes: file_request["internalNotes"] = internal_notes
        if show_creator is not None: file_request["showCreatorName"] = show_creator
        if show_creator_login is not None: file_request["showCreatorUsername"] = show_creator_login
        if max_slots: file_request["maxSlots"] = max_slots
        if max_size: file_request["maxSize"] = max_size
        if reset_max_slots is not None: file_request["resetSlots"] = reset_max_slots
        if reset_max_size is not None: file_request["resetSize"] = reset_max_size
        if language: file_request["receiverLangauge"] = language
        if show_uploaded_files is not None: file_request["showUploadedFiles"] = show_uploaded_files
        if sms_recipients: file_request["textMessageRecipients"] = sms_recipients

        return UpdateFileRequest(**file_request)

    # update a specific file request (given request ID)
    @validate_arguments
    async def update_file_request(self, file_request_id: int, file_request_update: UpdateFileRequest) -> UploadShare:
        """ update a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        payload = file_request_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Updating file request {file_request_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return UploadShare(**res.json())

    # delete specific file request (given request ID)
    @validate_arguments
    async def delete_file_request(self, file_request_id: int) -> None:
        """ delete a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Deleting file request {file_request_id} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None

    # send file request via email 
    @validate_arguments
    async def mail_file_request(self, file_request_id: int, send_file_request: SendShare) -> None:
        """ send a specific file request via email (by id) """
        payload = send_file_request.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/uploads/{str(file_request_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
        except httpx.HTTPStatusError as e:
            await self.dracoon.logout()
            raise httpx.RequestError(f'Sending file request {file_request_id} to {send_file_request.recipients} in DRACOON failed: {e.response.status_code} ({e.request.url})')

        return None
    
    def make_share_send(self, recipients: List[int], body: str, language: str = None) -> SendShare:
        """ make a payload for mail_share() or mail_file_request() """
        send_share = {
            "recipients": recipients,
            "body": body
        }

        if language: send_share["receiverLanguage"] = language

        return SendShare(**send_share)


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