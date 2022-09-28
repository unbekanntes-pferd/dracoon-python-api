"""
Async DRACOON shares adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

"""

from typing import List
import httpx
import logging
import urllib.parse
from pydantic import validate_arguments

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.crypto.models import FileKey, UserKeyPairContainer
from dracoon.errors import ClientDisconnectedError, InvalidClientError
from .models import CreateFileRequest, CreateShare, Expiration, SendShare, UpdateFileRequest, UpdateFileRequests, UpdateShare, UpdateShares
from .responses import DownloadShare, DownloadShareList, UploadShare, UploadShareList

class DRACOONShares:

    """
    API wrapper for DRACOON shares endpoint:
    Share and file request management - requires manage shares or file request permissions.
    """


    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        
        
        
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.shares')
        
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/shares'
            
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
            self.logger.debug("DRACOON shares adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    # get list of all (download) shares
    @validate_arguments
    async def get_shares(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> DownloadShareList:
        """ list (all) shares visible as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/downloads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting shares failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved shares.")
        return DownloadShareList(**res.json())

    # create a new (download) share - for model see documentation linked above
    @validate_arguments
    async def create_share(self, share: CreateShare, raise_on_err: bool = False) -> DownloadShare:
        """ create a new share """
        payload = share.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating share failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Created share.")
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
    async def delete_shares(self, share_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "shareIds": share_list
        }
        api_url = self.api_url + f'/downloads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting shares failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted share.")
        return None

    # get information about a specific share (given share ID)
    @validate_arguments
    async def get_share(self, share_id: int, raise_on_err: bool = False) -> DownloadShare:
        """ get information of a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting share failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved share.")
        return DownloadShare(**res.json())

    # update a list of shares (given share IDs)
    @validate_arguments
    async def update_shares(self, shares_update: UpdateShares, raise_on_err: bool = False) -> None:
        """ bulk update specific shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads'

        payload = shares_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating shares failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated shares.")
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
    async def update_share(self, share_id: int, share_update: UpdateShare, raise_on_err: bool = False) -> DownloadShare:
        """ update a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        payload = share_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating share failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Updated share.")
        return DownloadShare(**res.json())

    # delete specific share (given share ID)
    @validate_arguments
    async def delete_share(self, share_id: int, raise_on_err: bool = False) -> None:
        """ delete a specific share (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting share failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted share.")
        return None

    # send share via email 
    @validate_arguments
    async def mail_share(self, share_id: int, send_share: SendShare, raise_on_err: bool = False) -> None:
        """ send a specific share via email (by id) """
        payload = send_share.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Mailing share failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Mailed share.")
        return None


    # get list of all (download) shares
    @validate_arguments
    async def get_file_requests(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> UploadShareList:
        """ list all file requests visible as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/uploads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
          
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved file requests.")
        return UploadShareList(**res.json())

    # create a new file request - for model see documentation linked above
    @validate_arguments
    async def create_file_request(self, file_request: CreateFileRequest, raise_on_err: bool = False) -> UploadShare:
        """ create a new file request """
        payload = file_request.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Created file request.")
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
    async def delete_file_requests(self, file_request_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of shares (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "shareIds": file_request_list
        }
        api_url = self.api_url + f'/uploads'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting file requests failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted file requests.")
        return None

    # get information about a specific file request (given request ID)
    @validate_arguments
    async def get_file_request(self, file_request_id: int, raise_on_err: bool = False) -> UploadShare:
        """ get information of a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved file request.")
        return UploadShare(**res.json())

    # update a specific file request (given request ID)
    @validate_arguments
    async def update_file_requests(self, file_requests_update: UpdateFileRequests, raise_on_err: bool = False) -> None:
        """ bulk update specifics file requests (by ids) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads'

        payload = file_requests_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating file requests failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated file request.")
        return None

    def make_file_requests_update(self, file_requests_list = List[int], expiration: Expiration = None, file_expiration: int = None,
                          show_creator_name: bool = None, show_creator_login: bool = None, 
                          max_slots: int = None, max_size: int = None, show_uploaded_files: bool = None, reset_max_size: bool = True, 
                          reset_max_slots: bool = None, reset_file_expiration: bool = None, raise_on_err: bool = False) -> UpdateFileRequests:

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
    async def update_file_request(self, file_request_id: int, file_request_update: UpdateFileRequest, raise_on_err: bool = False) -> UploadShare:
        """ update a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        payload = file_request_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated file request.")
        return UploadShare(**res.json())

    # delete specific file request (given request ID)
    @validate_arguments
    async def delete_file_request(self, file_request_id: int, raise_on_err: bool = False) -> None:
        """ delete a specific file request (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted file request.")
        return None

    # send file request via email 
    @validate_arguments
    async def mail_file_request(self, file_request_id: int, send_file_request: SendShare, raise_on_err: bool = False) -> None:
        """ send a specific file request via email (by id) """
        payload = send_file_request.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}/email'

        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Mailing file request failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Mailed file request.")
        return None
    
    def make_share_send(self, recipients: List[int], body: str, language: str = None) -> SendShare:
        """ make a payload for mail_share() or mail_file_request() """
        send_share = {
            "recipients": recipients,
            "body": body
        }

        if language: send_share["receiverLanguage"] = language

        return SendShare(**send_share)