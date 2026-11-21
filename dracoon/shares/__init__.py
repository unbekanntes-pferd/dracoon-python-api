"""
Async DRACOON shares adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/shares

"""

from typing import List, Optional
import logging
import urllib.parse

from dracoon.client import DRACOONClient
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

        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    async def get_shares(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> Optional[DownloadShareList]:
        """ list (all) shares visible as authenticated user """
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/downloads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting shares failed.")
            return None
        
        self.logger.info("Retrieved shares.")
        return DownloadShareList(**res.json())

    async def create_share(self, share: CreateShare, raise_on_err: bool = False) -> Optional[DownloadShare]:
        """ create a new share """
        payload = share.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads'

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Creating share failed.")
            return None

        self.logger.info("Created share.")
        return DownloadShare(**res.json())

    def make_share(self, node_id: int, name: str = None, password: str = None, expiration: Expiration = None, notes: str = None, internal_notes: str = None, 
                   show_creator: bool = None, show_creator_login: bool = None, max_downloads: int = None, keypair: UserKeyPairContainer = None, file_key: FileKey = None, 
                   receiver_language: str = None, sms_recipients: List[str] = None) -> CreateShare:
        
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
        if receiver_language: share["receiverLanguage"] = receiver_language
        if sms_recipients: share["textMessageRecipients"] = sms_recipients

        return CreateShare(**share)

    async def delete_shares(self, share_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of shares (by ids) """
        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "shareIds": share_list
        }
        api_url = self.api_url + f'/downloads'

        res = await self.dracoon.request('DELETE', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting shares failed.")
            return None
        
        self.logger.info("Deleted share.")
        return None

    async def get_share(self, share_id: int, raise_on_err: bool = False) -> Optional[DownloadShare]:
        """ get information of a specific share (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting share failed.")
            return None
        
        self.logger.info("Retrieved share.")
        return DownloadShare(**res.json())

    async def update_shares(self, shares_update: UpdateShares, raise_on_err: bool = False) -> None:
        """ bulk update specific shares (by ids) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads'

        payload = shares_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating shares failed.")
            return None
        
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
                   receiver_language: str = None, sms_recipients: List[str] = None, default_country: str = None,
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
        if receiver_language: share_update["receiverLanguage"] = receiver_language
        if default_country: share_update["defaultCountry"] = default_country
        if sms_recipients: share_update["textMessageRecipients"] = sms_recipients
        if reset_max_downloads is not None: share_update["resetMaxDownloads"] = reset_max_downloads
        if reset_password is not None: share_update["resetPassword"] = reset_password

        return UpdateShare(**share_update)



    async def update_share(self, share_id: int, share_update: UpdateShare, raise_on_err: bool = False) -> Optional[DownloadShare]:
        """ update a specific share (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        payload = share_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating share failed.")
            return None

        self.logger.info("Updated share.")
        return DownloadShare(**res.json())

    async def delete_share(self, share_id: int, raise_on_err: bool = False) -> None:
        """ delete a specific share (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}'

        res = await self.dracoon.request('DELETE', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting share failed.")
            return None
        
        self.logger.info("Deleted share.")
        return None

    async def mail_share(self, share_id: int, send_share: SendShare, raise_on_err: bool = False) -> None:
        """ send a specific share via email (by id) """
        payload = send_share.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/downloads/{str(share_id)}/email'

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Mailing share failed.")
            return None
        
        self.logger.info("Mailed share.")
        return None


    async def get_file_requests(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> Optional[UploadShareList]:
        """ list all file requests visible as authenticated user """
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/uploads?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting file request failed.")
            return None
        
        self.logger.info("Retrieved file requests.")
        return UploadShareList(**res.json())

    async def create_file_request(self, file_request: CreateFileRequest, raise_on_err: bool = False) -> Optional[UploadShare]:
        """ create a new file request """
        payload = file_request.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads'

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Creating file request failed.")
            return None
        
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

    async def delete_file_requests(self, file_request_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of shares (by ids) """
        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "shareIds": file_request_list
        }
        api_url = self.api_url + f'/uploads'

        res = await self.dracoon.request('DELETE', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting file requests failed.")
            return None
        
        self.logger.info("Deleted file requests.")
        return None

    async def get_file_request(self, file_request_id: int, raise_on_err: bool = False) -> Optional[UploadShare]:
        """ get information of a specific file request (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting file request failed.")
            return None
        
        self.logger.info("Retrieved file request.")
        return UploadShare(**res.json())

    async def update_file_requests(self, file_requests_update: UpdateFileRequests, raise_on_err: bool = False) -> None:
        """ bulk update specifics file requests (by ids) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads'

        payload = file_requests_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating file requests failed.")
            return None
        
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

    async def update_file_request(self, file_request_id: int, file_request_update: UpdateFileRequest, raise_on_err: bool = False) -> Optional[UploadShare]:
        """ update a specific file request (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        payload = file_request_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating file request failed.")
            return None
        
        self.logger.info("Updated file request.")
        return UploadShare(**res.json())

    async def delete_file_request(self, file_request_id: int, raise_on_err: bool = False) -> None:
        """ delete a specific file request (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}'

        res = await self.dracoon.request('DELETE', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting file request failed.")
            return None
        
        self.logger.info("Deleted file request.")
        return None

    async def mail_file_request(self, file_request_id: int, send_file_request: SendShare, raise_on_err: bool = False) -> None:
        """ send a specific file request via email (by id) """
        payload = send_file_request.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/uploads/{str(file_request_id)}/email'

        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Mailing file request failed.")
            return None
        
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