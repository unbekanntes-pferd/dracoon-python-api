"""
Async DRACOON nodes adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for nodes management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/nodes

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""

import datetime
import os
import math
from pathlib import Path
from datetime import datetime
from typing import List, Union
import logging
import asyncio
import urllib.parse

import httpx
from pydantic import validate_arguments
from tqdm import tqdm

from dracoon.crypto import FileEncryptionCipher, encrypt_bytes, encrypt_file_key, create_file_key, get_file_key_version
from dracoon.crypto.models import FileKey, PlainUserKeyPairContainer, UserKeyPairContainer
from dracoon.groups.models import Expiration
from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.errors import (InvalidClientError, ClientDisconnectedError, InvalidFileError, InvalidArgumentError)
from dracoon.uploads.models import UploadChannelResponse
from .models import (Callback, CompleteS3Upload, CompleteUpload, ConfigRoom, CreateFolder, CreateRoom, CreateUploadChannel, EncryptRoom, 
                     GetS3Urls, LogEventList, MissingKeysResponse, Node, NodeItem, Permissions, ProcessRoomPendingUsers, S3Part, 
                     SetFileKeys, SetFileKeysItem, TransferNode, CommentNode, RestoreNode, UpdateFile, UpdateFiles, 
                     UpdateFolder, UpdateRoom, UpdateRoomGroupItem, UpdateRoomGroups, UpdateRoomHooks, 
                     UpdateRoomUserItem, UpdateRoomUsers)
from .responses import (Comment, CommentList, CreateFileUploadResponse, DeletedNode, DeletedNodeSummaryList, 
                       DeletedNodeVersionsList, DownloadTokenGenerateResponse, NodeList, NodeParentList, 
                       PendingAssignmentList, PresignedUrlList, RoomGroupList, RoomUserList, RoomWebhookList, 
                       S3FileUploadStatus, S3Status)

# constants for uploads 
CHUNK_SIZE = 33554432
#min chunk size S3
MIN_CHUNK_SIZE = 5242880
MAX_CHUNKS = 9999
POLL_WAIT = 0.1

class DRACOONNodes:

    """
    API wrapper for DRACOON nodes endpoint:
    Node operations (rooms, files, folders), room webhooks, comments and file transfer (up- and download)
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client')
        
        self.logger = logging.getLogger('dracoon.nodes')

        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/nodes'
            
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
            self.logger.debug("DRACOON nodes adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
    
    async def upload_bytes(self, file_obj, progress: tqdm = None, callback_fn: Callback  = None):
        """ async iterator to stream byte upload """
        while True:
            data = file_obj.read()
            if not data:
                break
            if progress: progress.update(len(data))
            if callback_fn: callback_fn(len(data))
            yield data
            
    def read_in_chunks(self, file_obj, chunksize: int = CHUNK_SIZE, progress: tqdm = None, callback_fn: Callback  = None):
        """ iterator to read a file object in chunks (default chunk size: 32 MB) """
        while True:
            data = file_obj.read(chunksize)
            if not data:
                break
            if progress: progress.update(len(data))
            if callback_fn: callback_fn(len(data))
            yield data
            
    async def byte_stream(self, data: bytes, progress: tqdm = None, callback_fn: Callback  = None):  
        """ stream bytes """   
        while True:
            if not data:
                break
            if progress: progress.update(len(data))
            if callback_fn: callback_fn(len(data))
            yield data

    # get download url as authenticated user to download a file
    @validate_arguments
    async def create_upload_channel(self, upload_channel: CreateUploadChannel, raise_on_err: bool = False) -> CreateFileUploadResponse:
        """ create an upload channel to upload (S3 direct or proxy) """
        payload = upload_channel.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + '/files/uploads'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating upload channel failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Upload channel created.")
        return CreateFileUploadResponse(**res.json())
    
    def make_upload_channel(self, parent_id: int, name: str, classification: int = None, size: int = None, expiration: Expiration = None, notes: str = None, 
                            direct_s3_upload: bool = None, modification_date: str = None, creation_date: str = None) -> CreateUploadChannel:
        """ make an upload channel payload for create_upload_channel() """
        
        upload_channel = {
            "parentId": parent_id,
            "name": name
        }
        
        if modification_date:  upload_channel["timestampModification"] = modification_date
        if creation_date:  upload_channel["timestampCreation"] = creation_date
        if classification: upload_channel["classification"] = classification
        if size: upload_channel["size"] = size
        if expiration: upload_channel["expiration"] = expiration
        if notes: upload_channel["notes"] = notes
        if direct_s3_upload is not None: upload_channel["directS3Upload"] = direct_s3_upload

        return CreateUploadChannel(**upload_channel)


    @validate_arguments
    async def cancel_upload(self, upload_id: str, raise_on_err: bool = False) -> None:
        """ cancel an upload channel (and delete chunks) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/uploads/{upload_id}'
        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Canceling upload failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Upload canceled.")
        return None

    async def get_node_from_path(self, path: str, filter: str = None, raise_on_err: bool = False) -> Node:
        """ get node id from path """
        
        # folder / room 
        if path[-1] == '/':
            last_node = path.split('/')[-2]
            parent_path = '/'.join(path.split('/')[:-2])
            depth = len(path.split('/')[:-1]) - 1
        # file
        else:
            last_node = path.split('/')[-1]
            parent_path = '/'.join(path.split('/')[:-1])
            depth = len(path.split('/')[:-1])

        filter_str = f'parentPath:eq:{parent_path}/'

        if filter: filter_str += f'|{filter}'
        
        filter_str = urllib.parse.quote(filter_str)
        last_node = urllib.parse.quote(last_node)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/search?search_string={last_node}&filter={filter_str}&depth_level={str(depth)}'

        try:
            res = await self.dracoon.http.get(url=api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Copying nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)


        if res.status_code == 200 and len(res.json()["items"]) > 0:
            self.logger.info("Retrieved node from path.")
            return Node(**res.json()["items"][0])
        else:
            self.logger.error("Node from path not found.")
            return None


    @validate_arguments
    async def complete_s3_upload(self, upload_id: str, upload: CompleteS3Upload, raise_on_err: bool = False) -> None:
        """ finalize an S3 direct upload """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/uploads/{upload_id}/s3'

        payload = upload.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Completing S3 upload failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Completed S3 upload.")
        
        # handle resolutionStrategy fail and raise_on_err True with conflict
        if res.status_code == 409:
            return res.json()
        
        return None

    def make_s3_upload_complete(self, parts: List[S3Part], resolution_strategy: str = None, keep_share_links: str = None, file_name: str = None, 
                                 file_key: FileKey = None) -> CompleteS3Upload:
        """ make payload required in complete_s3_upload() """
        s3_upload_complete = {
            "parts": parts
        }

        if resolution_strategy: s3_upload_complete["resolutionStrategy"] = resolution_strategy
        if keep_share_links: s3_upload_complete["keepShareLinks"] = keep_share_links
        if file_name: s3_upload_complete["fileName"] = file_name
        if file_key: s3_upload_complete["fileKey"] = file_key
  
        return CompleteS3Upload(**s3_upload_complete)
    
    def make_get_s3_urls(self, first_part: int, last_part: int, chunk_size: int = CHUNK_SIZE):
        
        payload = {
            "firstPartNumber": first_part,
            "lastPartNumber": last_part,
            "size": chunk_size
        }
        
        return GetS3Urls(**payload)

    @validate_arguments
    async def get_s3_urls(self, upload_id: str, upload: GetS3Urls, raise_on_err: bool = False) -> PresignedUrlList:
        """ get a list of S3 urls based on provided chunk count """
        """ chunk size needs to be larger than 5 MB """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/uploads/{upload_id}/s3_urls'

        payload = upload.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting S3 urls failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved S3 presigned upload URLs.")
        return PresignedUrlList(**res.json())
    
    async def upload_unencrypted(self, file_path: str, upload_channel: CreateFileUploadResponse, keep_shares: bool = False, 
                                    file_name: str = None, resolution_strategy: str = 'autorename', chunksize: int = CHUNK_SIZE, 
                                    display_progress: bool = False, raise_on_err: bool = False, 
                                    callback_fn: Callback  = None
                                    ) -> Node:
        if self.raise_on_err:
            raise_on_err = True 
            
        file = Path(file_path)
        if not file.is_file():
            self.logger.critical('File not found: %s', file_path)
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err=err)
        
        filesize = file.stat().st_size
        if file_name is None: 
            file_name = file.name
        
        # init callback size
        if callback_fn: callback_fn(0, filesize)
        
        if filesize <= chunksize:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None

            with open(file, 'rb') as f:
                         
                try:
                    res = await self.dracoon.uploader.post(url=upload_channel.uploadUrl, content=self.upload_bytes(file_obj=f, progress=progress, callback_fn=callback_fn))
                    res.raise_for_status()     
                    if display_progress: progress.update(filesize)
                except httpx.RequestError as e:
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_connection_error(e)
                except httpx.HTTPStatusError as e:
                    self.logger.error("Uploading file failed.")
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=True)
                finally: 
                    if display_progress: progress.close()
                    
        elif filesize > chunksize:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
                

            with open(file, 'rb') as f:
                
                index = 0
                offset = 0
                                         
                for chunk in self.read_in_chunks(file_obj=f, chunksize=chunksize, progress=progress, callback_fn=callback_fn):
                                          
                    upload_url = upload_channel.uploadUrl
                    content_range = f'bytes {index}-{offset}/{filesize}'
                    
                    upload_file = {
                    'file': chunk
                        }
                    
                    index = offset 
                    
                    try:        

                        self.dracoon.uploader.headers["Content-Range"] = content_range
                        res = await self.dracoon.uploader.post(url=upload_url, files=upload_file) 
                        res.raise_for_status()

                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_connection_error(e)
                        if display_progress: progress.close()
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        self.logger.error("Uploading chunk failed.")
                        await self.dracoon.handle_http_error(err=e, raise_on_err=True)
                        if display_progress: progress.close()

         
                if display_progress: progress.close()             
                    
        complete_upload = self.make_upload_complete(file_name=file_name, keep_shares=keep_shares, 
                                                   resolution_strategy=resolution_strategy)
 
        node = await self.complete_upload(upload_channel=upload_channel, payload=complete_upload, raise_on_err=raise_on_err)
             
        return node
    
                                  
    async def upload_encrypted(self, file_path: str, upload_channel: CreateFileUploadResponse, plain_keypair: PlainUserKeyPairContainer, 
                                  file_name: str = None, keep_shares: bool = False, resolution_strategy: str = 'autorename', 
                                  chunksize: int = CHUNK_SIZE, display_progress: bool = False, raise_on_err: bool = False,
                                  callback_fn: Callback  = None
                                  ) -> Node:
        if self.raise_on_err:
            raise_on_err = True 
            
        file = Path(file_path)
        if not file.is_file():
            self.logger.critical('File not found: %s', file_path)
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err=err)
        
        filesize = file.stat().st_size
        if file_name is None: 
            file_name = file.name
        
        # init callback size
        if callback_fn: callback_fn(0, filesize)
        
        if filesize <= chunksize:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
                
            plain_file_key = create_file_key()

            with open(file, 'rb') as f:
                
                enc_bytes, plain_file_key = encrypt_bytes(plain_data=f.read(), plain_file_key=plain_file_key)
                
                files = {
                    "file": enc_bytes
                }
                     
                try:
                    res = await self.dracoon.uploader.post(url=upload_channel.uploadUrl, files=files)
                    res.raise_for_status()
                    if display_progress: progress.update(filesize)
                    if callback_fn: callback_fn(filesize)
                except httpx.RequestError as e:
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_connection_error(e)
                except httpx.HTTPStatusError as e:
                    self.logger.error("Uploading file failed.")
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=True)
                finally: 
                    if display_progress: progress.close()
                    
        elif filesize > chunksize:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
                

            with open(file, 'rb') as f:
                
                index = 0
                offset = 0
                
                plain_file_key = create_file_key()
                
                dracoon_cipher = FileEncryptionCipher(plain_file_key=plain_file_key)
                                         
                for chunk in self.read_in_chunks(file_obj=f, chunksize=chunksize, progress=progress, callback_fn=callback_fn):
                                          
                    upload_url = upload_channel.uploadUrl
                    content_range = f'bytes {index}-{offset}/{filesize}'
                
                    # if not las chunk
                    if filesize - offset > chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                    
                    # last chunk needs to include the final data 
                    elif filesize - offset <= chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                        last_chunk, plain_file_key = dracoon_cipher.finalize() 
                        enc_chunk += last_chunk
                                                
                    offset = index + len(enc_chunk)
                    index = offset
                    
                    upload_file = {
                    'file': enc_chunk
                        }
                    
                    
                    try:                              
                        self.dracoon.uploader.headers["Content-Range"] = content_range                    
                        res = await self.dracoon.uploader.post(url=upload_url, files=upload_file) 
                        res.raise_for_status()

                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_connection_error(e)
                        if display_progress: progress.close()
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        self.logger.error("Uploading chunk failed.")
                        await self.dracoon.handle_http_error(err=e, raise_on_err=True)
                        if display_progress: progress.close()

                if display_progress: progress.close()
                    

        # encrypt file key    
        file_key = encrypt_file_key(plain_file_key=plain_file_key, keypair=plain_keypair)
        
        # handle file conflicts on raise_on_err False
        if res.status_code == 409 and resolution_strategy == 'fail':
            self.logger.debug('Upload failed: File already exists')
            return
        
        complete_upload = self.make_upload_complete(file_name=file_name, keep_shares=keep_shares, 
                                                   resolution_strategy=resolution_strategy, file_key=file_key)
        
        node = await self.complete_upload(upload_channel=upload_channel, payload=complete_upload, raise_on_err=raise_on_err)
             
        return node
    
    def make_upload_complete(self, resolution_strategy: str = 'autorename', keep_shares: bool = False,
                             file_name: str = None, file_key: FileKey = None) -> CompleteUpload:
        
        payload = {
            "resolutionStrategy": resolution_strategy,
            "keepShareLinks": keep_shares    
        }
        
        if file_name is not None:
            payload["fileName"] = file_name
        
        if file_key is not None:
            payload["fileKey"] = file_key
            
        
        return CompleteUpload(**payload)
            
    async def complete_upload(self, upload_channel: UploadChannelResponse, payload: CompleteUpload, raise_on_err: bool = False) -> Node:
        
        api_url = self.dracoon.base_url + self.dracoon.api_base_url + f'/uploads/{upload_channel.token}'
        
        try:
            res = await self.dracoon.http.put(api_url, json=payload.dict(exclude_unset=True))
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.http.delete(upload_channel.uploadUrl)
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Uploading file failed.")
            await self.dracoon.http.delete(upload_channel.uploadUrl)
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
          
        return Node(**res.json())
    
    async def upload_s3_unencrypted(self, file_path: str, upload_channel: CreateFileUploadResponse, keep_shares: bool = False,
                                    file_name: str = None,
                                    resolution_strategy: str = 'autorename', chunksize: int = CHUNK_SIZE, 
                                    display_progress: bool = False, raise_on_err: bool = False, 
                                    callback_fn: Callback  = None) -> S3FileUploadStatus:
        if self.raise_on_err:
            raise_on_err = True

        """ Check if file is file """

        file = Path(file_path)
        
        if not file.is_file():
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err)
        
        filesize = file.stat().st_size
        if file_name is None: 
            file_name = file.name
        
        # init callback size
        if callback_fn: callback_fn(0, filesize)
        
        self.logger.debug("File name: %s", file_name)
        self.logger.debug("File size: %s", filesize)
        

        part_count = math.ceil(filesize / chunksize)
        
        # handle 0KB files
        if part_count == 0:
            part_count = 1
        
        if part_count == 1:
            chunksize = filesize
            s3_upload = self.make_get_s3_urls(first_part=1, last_part=part_count, chunk_size=chunksize)
        else:
            last_chunk = filesize - ((part_count - 1) * chunksize)
            s3_upload = self.make_get_s3_urls(first_part=1, last_part=(part_count - 1), chunk_size=chunksize)
            s3_upload_final = self.make_get_s3_urls(first_part=part_count, last_part=part_count, chunk_size=last_chunk)
            final_s3_url = await self.get_s3_urls(upload_id=upload_channel.uploadId, upload=s3_upload_final, raise_on_err=raise_on_err)
        
        
        s3_urls = await self.get_s3_urls(upload_id=upload_channel.uploadId, upload=s3_upload, raise_on_err=raise_on_err)
        
        if part_count > 1:
            s3_urls.urls.append(final_s3_url.urls[0])
        
        
        self.logger.debug("Parts: %s", part_count)

        if len(s3_urls.urls) > MAX_CHUNKS:
            err = InvalidArgumentError(message=f'Maximum count of chunks ({MAX_CHUNKS}) exceeded.')
            await self.dracoon.handle_generic_error(err)
            
       
        parts = []
        
        # single part upload
        if part_count == 1:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
            
            with open(file, 'rb') as f:
                         
                try:
                    self.dracoon.uploader.headers["Content-Length"] = str(filesize)
                    res = await self.dracoon.uploader.put(url=s3_urls.urls[0].url, content=self.upload_bytes(file_obj=f, progress=progress, callback_fn=callback_fn))
                    res.raise_for_status()
                        
                    # remove double quotes from etag
                    e_tag = res.headers["ETag"].replace('"', '')
                    part = S3Part(**{ "partNumber": 1, "partEtag": e_tag })
                    parts.append(part)
                        
                    if display_progress: progress.update(filesize)
                except httpx.RequestError as e:
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_connection_error(e)
                except httpx.HTTPStatusError as e:
                    self.logger.error("Uploading file failed.")
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=True, is_xml=True)
                finally: 
                    if display_progress: progress.close()

           
        elif part_count > 1:
            
            if display_progress: 
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
            
            with open(file, 'rb') as f:
                
                part_number = 0
                                         
                for chunk in self.read_in_chunks(file_obj=f, chunksize=chunksize, progress=progress, callback_fn=callback_fn):
                                          
                    upload_url = s3_urls.urls[part_number].url

                    try:        
                        self.dracoon.uploader.headers["Content-Length"] = str(len(chunk)) 
                            
                        res = await self.dracoon.uploader.put(url=upload_url, content=chunk)
                            
                        res.raise_for_status()
                        e_tag = res.headers["ETag"].replace('"', '')
                        part = S3Part(**{ "partNumber": s3_urls.urls[part_number].partNumber, "partEtag": e_tag })
                        parts.append(part)
                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_connection_error(e)
                        if display_progress: progress.close()
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        self.logger.error("Uploading chunk failed.")
                        await self.dracoon.handle_http_error(err=e, raise_on_err=True, is_xml=True)
                        if display_progress: progress.close()

                    part_number += 1
                    
                if display_progress: progress.close()
                    
        s3_complete = self.make_s3_upload_complete(parts=parts, file_name=file_name, keep_share_links=keep_shares, 
                                                   resolution_strategy=resolution_strategy)
 
        upload = await self.complete_s3_upload(upload_id=upload_channel.uploadId, upload=s3_complete, raise_on_err=raise_on_err)
        
        # handle resolutionStrategy fail and raise_on_err True with conflict  (409)
        if upload is not None:         
            return 
        
        time  = POLL_WAIT
        
        while True:
            upload_status = await self.check_s3_upload(upload_id=upload_channel.uploadId, raise_on_err=raise_on_err)
            if upload_status.status == S3Status.done.value:
                break
            if upload_status.status == S3Status.error.value:
                break
            # wait until next request
            await asyncio.sleep(time)
            # increase wait 
            time *= 2
            
        return upload_status
        
    async def upload_s3_encrypted(self, file_path: str, upload_channel: CreateFileUploadResponse, plain_keypair: PlainUserKeyPairContainer, 
                                  file_name: str = None,
                                  keep_shares: bool = False, resolution_strategy: str = 'autorename', 
                                  chunksize: int = CHUNK_SIZE, display_progress: bool = False, raise_on_err: bool = False,
                                  callback_fn: Callback  = None
                                  ) -> S3FileUploadStatus:
        
        """ Upload a file into an encrypted container via S3 direct upload """
        
        if self.raise_on_err:
            raise_on_err = True

        file = Path(file_path)
        
        # check if file is a file
        if not file.is_file():
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err)
        

        #init callback size
        
        filesize = file.stat().st_size
        if file_name is None: 
            file_name = file.name
            
        if callback_fn: callback_fn(0, filesize)
        self.logger.debug("File name: %s", file_name)
        self.logger.debug("File size: %s", filesize)
         
        # create file key
        plain_file_key = create_file_key()
        
        # calculate required parts based on chunk size
        part_count = math.ceil(filesize / chunksize)
        
        # handle 0KB file 
        if part_count == 0:
            part_count = 1
        
        if part_count == 1:
            chunksize = filesize
            s3_upload = self.make_get_s3_urls(first_part=1, last_part=part_count, chunk_size=chunksize)
        else:
            last_chunk = filesize - ((part_count - 1) * chunksize)
            s3_upload = self.make_get_s3_urls(first_part=1, last_part=(part_count - 1), chunk_size=chunksize)
            s3_upload_final = self.make_get_s3_urls(first_part=part_count, last_part=part_count, chunk_size=last_chunk)
            final_s3_url = await self.get_s3_urls(upload_id=upload_channel.uploadId, upload=s3_upload_final, raise_on_err=raise_on_err)
        
        
        s3_urls = await self.get_s3_urls(upload_id=upload_channel.uploadId, upload=s3_upload, raise_on_err=raise_on_err)
        
        if part_count > 1:
            s3_urls.urls.append(final_s3_url.urls[0])
        
        
        self.logger.debug("Parts: %s", part_count)

        if len(s3_urls.urls) > MAX_CHUNKS:
            err = InvalidArgumentError(message=f'Maximum count of chunks ({MAX_CHUNKS}) exceeded.')
            await self.dracoon.handle_generic_error(err)
            
        parts = []
        
        # single part upload
        if part_count == 1:
            
            if display_progress:
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
            
            with open(file, 'rb') as f:
                
                enc_bytes, plain_file_key = encrypt_bytes(plain_data=f.read(), plain_file_key=plain_file_key)
                         
                try:

                    self.dracoon.uploader.headers["Content-Length"] = str(len(enc_bytes))
                    res = await self.dracoon.uploader.put(url=s3_urls.urls[0].url, content=enc_bytes)
                    res.raise_for_status()
                        
                    # remove double quotes from etag
                    e_tag = res.headers["ETag"].replace('"', '')
                    part = S3Part(**{ "partNumber": 1, "partEtag": e_tag })
                    parts.append(part)
                    if display_progress: progress.update(filesize)
                    if callback_fn: callback_fn(filesize)
                except httpx.RequestError as e:
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_connection_error(e)
                except httpx.HTTPStatusError as e:
                    self.logger.error("Uploading file failed.")
                    res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=True, is_xml=True)
                finally: 
                    if display_progress: progress.close()

        # multipart upload
        elif part_count > 1:
            
            if display_progress:
                progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True, desc=file_name)
            else:
                progress = None
            
            with open(file, 'rb') as f:
                
                part_number = 0
                offset = 0
                index = 0
                
                dracoon_cipher = FileEncryptionCipher(plain_file_key=plain_file_key)
                                    
                for chunk in self.read_in_chunks(file_obj=f, chunksize=chunksize, progress=progress, callback_fn=callback_fn):
                    
                    # if not las chunk
                    if filesize - offset > chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                    
                    # last chunk needs to include the final data 
                    elif filesize - offset <= chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                        last_chunk, plain_file_key = dracoon_cipher.finalize() 
                        enc_chunk += last_chunk
                                          
                    upload_url = s3_urls.urls[part_number].url
                    
                    offset = index + len(enc_chunk)
                    index = offset
                
                    try:        
                        self.dracoon.uploader.headers["Content-Length"] = str(len(enc_chunk)) 
                        res = await self.dracoon.uploader.put(url=upload_url, content=enc_chunk)
                        res.raise_for_status()
                        e_tag = res.headers["ETag"].replace('"', '')
                        part = S3Part(**{ "partNumber": s3_urls.urls[part_number].partNumber, "partEtag": e_tag })
                        parts.append(part)
                        self.logger.debug("Uploaded part %s", part_number)
                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        if progress: progress.close()
                        await self.dracoon.handle_connection_error(e)
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        self.logger.error("Uploading chunk failed.")
                        if progress: progress.close()
                        await self.dracoon.handle_http_error(err=e, raise_on_err=True, is_xml=True)

                    part_number += 1
                    
                if progress: progress.close()
                
        # encrypt file key    
        file_key = encrypt_file_key(plain_file_key=plain_file_key, keypair=plain_keypair)
        
        s3_complete = self.make_s3_upload_complete(parts=parts, file_name=file_name, keep_share_links=keep_shares, 
                                                   resolution_strategy=resolution_strategy, file_key=file_key)
 
        upload = await self.complete_s3_upload(upload_id=upload_channel.uploadId, upload=s3_complete, raise_on_err=raise_on_err)
        
        # handle resolutionStrategy fail and raise_on_err True with conflict (409)
        if upload is not None:         
            return 
        
        time  = POLL_WAIT 
        
        while True:
            upload_status = await self.check_s3_upload(upload_id=upload_channel.uploadId, raise_on_err=raise_on_err)
            if upload_status.status == S3Status.done.value:
                break
            if upload_status.status == S3Status.error.value:
                break
            # wait until next request
            await asyncio.sleep(time)
            # increase wait 
            time *= 2
            
        return upload_status
            
    async def check_s3_upload(self, upload_id: str, raise_on_err: bool = False) -> S3FileUploadStatus:
        """ check status of S3 upload """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
        
        api_url = self.api_url + f'/files/uploads/{upload_id}'
        
        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Checking S3 upload failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
            
        self.logger.info("Retrieved S3 upload status.")
        return S3FileUploadStatus(**res.json())
        

    @validate_arguments
    async def get_nodes(self, room_manager: bool = False, parent_id: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, 
                        raise_on_err: bool = False) -> NodeList:
        """ list (all) visible nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
            
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + \
            f'/?offset={offset}&parent_id={str(parent_id)}&room_manager={str(room_manager).lower()}'
        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved nodes.")
        return NodeList(**res.json())
    
    # delete nodes for given array of node ids
    @validate_arguments
    async def delete_nodes(self, node_list: List[int], raise_on_err: bool = False) -> None:
        """ delete a list of nodes (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "nodeIds": node_list
        }

        try:
            res = await self.dracoon.http.request(method='DELETE', url=self.api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Deleted node(s).")
        return None

    # get node for given node id
    @validate_arguments
    async def get_node(self, node_id: int, raise_on_err: bool = False) -> Node:
        """ get specific node details (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(node_id)}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting node failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node.")
        return Node(**res.json())


    @validate_arguments
    async def delete_node(self, node_id: int, raise_on_err: bool = False) -> None:
        """ delete specific node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(node_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting node failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted node.")
        return None

    # get node comments for given node id
    @validate_arguments
    async def get_node_comments(self, node_id: int, offset: int = 0, raise_on_err: bool = False) -> CommentList:
        """ get comments for specific node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + \
            f'/{str(node_id)}/comments/?offset={str(offset)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting node comments failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node comments.")
        return CommentList(**res.json())

    # get node for given node id
    @validate_arguments
    async def add_node_comment(self, node_id: int, comment: CommentNode, raise_on_err: bool = False) -> Comment:
        """ add a comment to a node """
        payload = comment.dict(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}/comments'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Adding node comment failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Added node comment.")
        return Comment(**res.json())

    def make_comment(self, text: str) -> CommentNode:
        """ make a comment payload for add_comment() """
        comment = {
            "text": text
        }

        return CommentNode(**comment)

    # copy node for given node id
    @validate_arguments
    async def copy_nodes(self, target_id: int, copy_node: TransferNode, raise_on_err: bool = False) -> Node:
        """ copy node(s) to given target id """
        payload = copy_node.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(target_id)}/copy_to'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Copying nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Copied nodes.")
        return Node(**res.json())
    

    def make_node_transfer(self, items: List[NodeItem], resolution_strategy: str = None, keep_share_links: bool = None, parent_id: int = None) -> TransferNode:
        """ make a node transfer payload for copy_nodes() and move_nodes() """
        node_transfer = {
            "items": items
        }

        if resolution_strategy is not None: node_transfer["resolutionStrategy"] = resolution_strategy
        if keep_share_links is not None: node_transfer["keepShareLinks"] = keep_share_links
        if parent_id is not None: node_transfer["parentId"] = parent_id
        
        return TransferNode(**node_transfer)
    
    def make_node_item(self, node_id: int, name: str = None, modified_date: str = None, created_date: str = None) -> NodeItem:
        
        node_item = {
            "id": node_id
        }
        
        if name: node_item["name"] = name
        if modified_date: node_item["timestampModification"] = modified_date
        if created_date: node_item["timestampCreation"] = created_date
        
        return NodeItem(**node_item)

    # get node comfor given node id
    @validate_arguments
    async def get_deleted_nodes(self, parent_id: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> DeletedNodeSummaryList:
        """ list (all) deleted nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
            
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + \
            f'/{str(parent_id)}/deleted_nodes/?offset={offset}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting deleted nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved deleted nodes.")
        return DeletedNodeSummaryList(**res.json())


    @validate_arguments
    async def empty_node_recyclebin(self, parent_id: int, raise_on_err: bool = False) -> None:
        """ delete all nodes in recycle bin of parent (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(parent_id)}/deleted_nodes'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Emptying node recycle bin failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Emptied node recycle bin.")
        return None

    # get node versions in a given parent id (requires name, specification of type)
    @validate_arguments
    async def get_node_versions(self, parent_id: int, name: str, type: str, offset: int = 0, raise_on_err: bool = False) -> DeletedNodeVersionsList:
        """ get (all) versions of a node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        name = urllib.parse.quote(name)
        
        api_url = self.api_url + f'/{str(parent_id)}/deleted_nodes/versions?name={name}&type={type}&offset={offset}'

        try:
            res = await self.dracoon.http.get(api_url)
        
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting node versions failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node versions.")
        return DeletedNodeVersionsList(**res.json())


    @validate_arguments
    async def add_favorite(self, node_id: int, raise_on_err: bool = False) -> Node:
        """ add a specific node to favorites (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(node_id)}/favorite'
        try:
            res = await self.dracoon.http.post(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Adding favorite failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Added node to favorites.")
        return Node(**res.json())

    # delete node for given node id
    @validate_arguments
    async def delete_favorite(self, node_id: int, raise_on_err: bool = False) -> None:
        """ remove a specific node from favorites (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(node_id)}/favorite'

        try:
            res = await self.dracoon.http.delete(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting favorite failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        self.logger.info("Removed node from favorites.")
        return None

    # copy node for given node id
    @validate_arguments
    async def move_nodes(self, target_id: int, move_node: TransferNode, raise_on_err: bool = False) -> Node:
        """ move node(s) to target node (by id) """
        payload = move_node.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(target_id)}/move_to'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Moving nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
            self.logger.info("Moved node(s).")
        return Node(**res.json())


    # get node ancestors (parents)
    @validate_arguments
    async def get_parents(self, node_id: int, raise_on_err: bool = False) -> NodeParentList:
        """ get node parents """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/{str(node_id)}/parents'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting parents failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node parents.")
        return NodeParentList(**res.json())

    # delete deleted nodes in recycle bin for given array of node ids

    @validate_arguments
    async def empty_recyclebin(self, node_list: List[int], raise_on_err: bool = False) -> None:
        """ empty recylce bin: list of nodes (deleted nodes by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "deletedNodeIds": node_list
        }
        
        api_url = self.api_url + '/deleted_nodes'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Emptying recycle bin failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Emptied recycle bin.")
        return None

    @validate_arguments
    async def get_deleted_node(self, node_id: int, raise_on_err: bool = False) -> DeletedNode:
        """ get details of a specific deleted node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/deleted_nodes/{str(node_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting deleted node failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved deleted node.")
        return DeletedNode(**res.json())


    @validate_arguments
    async def restore_nodes(self, restore: RestoreNode, raise_on_err: bool = False) -> None:
        """ restore a list of nodes from recycle bin """
        payload = restore.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/deleted_nodes/actions/restore'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Restoring nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Restored deleted node(s).")
        return None

    def make_node_restore(self, deleted_node_list: List[int], resolution_strategy: str = None, keep_share_links: bool = None, 
                        parent_id: int = None) -> RestoreNode:
        """ make payload required for restore_nodes() """
        node_restore = {
            "deletedNodeIds": deleted_node_list
        }

        if resolution_strategy: node_restore["resolutionStrategy"] = resolution_strategy
        if keep_share_links is not None: node_restore["keepShareLinks"] = keep_share_links
        if parent_id: node_restore["parentId"] = parent_id
        
        return RestoreNode(**node_restore)

    # update file meta data
    @validate_arguments
    async def update_file(self, file_id: int, file_update: UpdateFile, raise_on_err: bool = False) -> Node:
        """ update file metadata """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/{str(file_id)}'

        payload = file_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating file failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated file.")
        return Node(**res.json())

    @validate_arguments
    async def update_files(self, files_update: UpdateFiles, raise_on_err: bool = False) -> None:
        """ update file metadata """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files'

        payload = files_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating files failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        self.logger.info("Updated file(s).")
        return None
    
    def make_file_update(self, name: str = None, classification: int = None, notes: str = None, expiration: Expiration = None, 
                               modified_date: str = None, created_date: str = None):
        
        update_file = {
            "name": name,
            "classification": classification,
            "notes": notes,
            "expiration": expiration,
            "timestampModification": modified_date,
            "timestampCreation": created_date
        }
        
        if all(update_file[key] is None for key in update_file.keys()):
            raise InvalidArgumentError(message="Payload is empty.")
        
        return UpdateFile(**update_file)
    
    def make_files_update(self, files: List[int], classification: int = None, expiration: Expiration = None):
        
        update_files = {
            "objectIds": files,
            "classification": classification,
            "expiration": expiration,
        }
        
        if all(update_files[key] is None for key in update_files.keys()):
            raise InvalidArgumentError(message="Payload is empty.")
        
        return UpdateFiles(**update_files)
    

    @validate_arguments
    async def get_download_url(self, node_id: int, raise_on_err: bool = False) -> DownloadTokenGenerateResponse:
        """ get download url for a specific node """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/{str(node_id)}/downloads'
        try:
            res = await self.dracoon.http.post(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting download URL failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        self.logger.info("Retrieved download URL.")
        return DownloadTokenGenerateResponse(**res.json())

    # get user file key if available
    @validate_arguments
    async def get_user_file_key(self, file_id: int, version: str = None, raise_on_err: bool = False) -> FileKey:
        """ get file key for given node as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/{str(file_id)}/user_file_key'

        if version: api_url += f'/?version={version}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating folder failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Retrieved user file key.")
        return FileKey(**res.json())

    @validate_arguments
    async def set_file_keys(self, file_keys: SetFileKeys, raise_on_err: bool = False) -> None:
        """ set file keys for nodes """
        payload = file_keys.dict(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/keys'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Setting file keys failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Set file key(s).")
        return None

    def make_set_file_keys(self, file_key_list: List[SetFileKeysItem], raise_on_err: bool = False) -> SetFileKeys:
        """ make payload required for set_file_keys() """
        return SetFileKeys(**{
            "items": file_key_list
        })
        

    def make_set_file_key_item(self, file_id: int, user_id: int, file_key: FileKey) -> SetFileKeysItem:
        """ make an entry to set a file key for a given file – required in make_set_file_keys() """
      
        return SetFileKeysItem(**{
            "fileId": file_id,
            "userId": user_id, 
            "fileKey": file_key
        })
        
    async def get_file_versions(self, reference_id: int, raise_on_err: bool = False):
        """ get all file versions (including deleted nodes) for given reference id """
        
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/files/versions/{str(reference_id)}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting node failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved node.")
        return Node(**res.json())

    @validate_arguments
    async def create_folder(self, folder: CreateFolder, raise_on_err: bool = False) -> Node:
        """ create a new folder """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/folders'

        payload = folder.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating folder failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Created folder.")
        return Node(**res.json())

    def make_folder(self, name: str, parent_id: int, notes: str = None, creation_date: str = None, modified_date: str = None) -> CreateFolder:
        """ make a folder payload required for create_folder() """
        folder = {
            "parentId": parent_id,
            "name": name
        }

        if notes: folder["notes"] = notes
        if creation_date: folder["timestampCreation"] = creation_date
        if modified_date: folder["timestampModification"] = modified_date

        return CreateFolder(**folder)

    def make_folder_update(self, name: str = None, notes: str = None, creation_date: str = None, modified_date: str = None) -> UpdateFolder:
        """" make a folder update payload for update_folder() """
        folder = {}
        
        if name: folder["name"] = name
        if notes: folder["notes"] = notes
        if creation_date: folder["timestampCreation"] = creation_date
        if modified_date: folder["timestampModification"] = modified_date

        return UpdateFolder(**folder)

    # update folder mets data
    @validate_arguments
    async def update_folder(self, node_id: int, folder_update: UpdateFolder, raise_on_err: bool = False) -> Node:
        """ update a folder """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/folders/{str(node_id)}'

        payload = folder_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating folder failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated folder.")
        return Node(**res.json())

    # get missing file keys
    @validate_arguments
    async def get_missing_file_keys(self, file_id: int = None, room_id: int = None, user_id: int = None, use_key: str = None, 
                                      offset: int = 0, limit: int = None, raise_on_err: bool = False) -> MissingKeysResponse:
        """ get (all) missing file keys """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/missingFileKeys/?offset={str(offset)}'

        if file_id != None:
            api_url += f'&file_id={str(file_id)}'
        if room_id != None:
            api_url += f'&room_id={str(room_id)}'
        if user_id != None:
            api_url += f'&user_id={str(user_id)}'
        if use_key != None:
            api_url += f'&use_key={use_key}'
        if limit != None:
            api_url += f'&limit={str(limit)}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()

        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting missing file keys failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved missing file keys.")
        return MissingKeysResponse(**res.json())

    # create room
    @validate_arguments
    async def create_room(self, room: CreateRoom, raise_on_err: bool = False) -> Node:
        """ create a new room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms'

        payload = room.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating room failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Created room.")
        return Node(**res.json())
    

    # update room mets data
    @validate_arguments
    async def update_room(self, node_id: int, room_update: UpdateRoom, raise_on_err: bool = False) -> Node:
        """ update a room (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(node_id)}'

        payload = room_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating room failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Updated room.")
        return Node(**res.json())

    def make_room(self, name: str, parent_id: int = None, notes: str = None, creation_date: str = None, modified_date: str = None,
                  quota: int = None, recycle_bin_period: int = None, inherit_perms: bool = None, classification: int = None, 
                  admin_ids: List[int] = None, admin_group_ids: List[int] = None, activities_log: bool = None,
                  new_group_member_acceptance: str = None) -> CreateRoom:
        """ make a room payload required for create_room() """
        room = {
            "name": name
        }
        
        if parent_id: room["parentId"] = parent_id
        if new_group_member_acceptance: room["newGroupMemberAcceptance"] = new_group_member_acceptance
        if quota: room["quota"] = quota
        if recycle_bin_period: room["recycleBinRetentionPeriod"] = recycle_bin_period
        if inherit_perms is not None: room["inheritPermissions"] = inherit_perms
        if activities_log: room["hasActivitiesLog"] = activities_log
        if admin_ids: room["adminIds"] = admin_ids
        if admin_group_ids: room["adminGroupIds"] = admin_group_ids
        if notes: room["notes"] = notes
        if creation_date: room["timestampCreation"] = creation_date
        if modified_date: room["timestampModification"] = modified_date
        if classification: room["classification"] = classification

        if not admin_ids and not admin_group_ids and inherit_perms is False:
            raise InvalidArgumentError(message='Room admin required: Please provide at least one room admin.')

        return CreateRoom(**room)

    def make_room_update(self, name: str = None, notes: str = None, quota: int = None, creation_date: str = None, modified_date: str = None) -> UpdateRoom:
        """ make a room update payload for update_room() """
        room = {}
        
        if name: room["name"] = name
        if notes: room["notes"] = notes
        if quota: room["quota"] = quota
        if creation_date: room["timestampCreation"] = creation_date
        if modified_date: room["timestampModification"] = modified_date

        return UpdateRoom(**room)

    # configure data room
    @validate_arguments
    async def config_room(self, node_id: int, config_update: ConfigRoom, raise_on_err: bool = False) -> Node:
        """ configure a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(node_id)}/config'

        payload = config_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Configuring room failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Configured room.")
        return Node(**res.json())

    def make_room_config(self, name: str = None, notes: str = None, created: datetime = None, updated: datetime = None, 
                        quota: int = None, recycle_bin_period: int = None, inherit_perms: bool = None, classification: int = None, 
                        admin_ids: List[int] = None, admin_group_ids: List[int] = None, activities_log: bool = None, 
                        new_group_member_acceptance: str = None) -> ConfigRoom:
        """ make a room config payload required for config_room() """
        room = {}
        
        if new_group_member_acceptance: room["newGroupMemberAcceptance"] = new_group_member_acceptance
        if quota: room["quota"] = quota
        if classification: room["classification"] = classification
        if recycle_bin_period: room["recycleBinRetentionPeriod"] = recycle_bin_period
        if inherit_perms is not None: room["inheritPermissions"] = inherit_perms
        if activities_log is not None: room["hasActivitiesLog"] = activities_log
        if admin_ids: room["adminIds"] = admin_ids
        if admin_group_ids: room["adminGroupIds"] = admin_group_ids
        if notes: room["notes"] = notes
        if created: room["timestampCreation"] = created
        if updated: room["timestampModification"] = updated
        if name: room["name"] = name

        return ConfigRoom(**room)

    def make_permissions(self, manage: bool, read: bool = True, create: bool = True,
                         change: bool = True, delete: bool = True, manage_shares: bool = True,
                         manage_file_requests: bool = True, read_recycle_bin: bool = True, 
                         restore_recycle_bin: bool = True, delete_recycle_bin: bool = False) -> Permissions:
        """ create a set of permissions for a room """
        return Permissions(**{
                             "manage": manage,
                             "read": read,
                             "create": create,
                             "change": change,
                             "delete": delete,
                             "manageDownloadShare": manage_shares,
                             "manageUploadShare": manage_file_requests,
                             "readRecycleBin": read_recycle_bin,
                             "restoreRecycleBin": restore_recycle_bin,
                             "deleteRecycleBin": delete_recycle_bin
                         })

    def make_permission_update(self, id: int, permission: Permissions) -> Union[UpdateRoomUserItem, UpdateRoomGroupItem]:
        """ make a permission update payload """
        
        return {
            "id": id,
            "permissions": permission

        }
    
    @validate_arguments
    def make_encrypt_room(self, is_encrypted: bool, use_sytem_rescue_key: bool = None, room_rescue_key: UserKeyPairContainer = None) -> EncryptRoom:
        """ make room encryption payload """
        
        encrypt_room = {
            "isEncrypted": is_encrypted
        }
        
        if use_sytem_rescue_key is not None: encrypt_room["useDataSpaceRescueKey"] = use_sytem_rescue_key
        if room_rescue_key: encrypt_room["dataRoomRescueKey"] = room_rescue_key
        
        return encrypt_room
    
    @validate_arguments
    async def encrypt_room(self, room_id: int, encrypt_room: EncryptRoom, raise_on_err: bool = False) -> Node:
        
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
        
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(room_id)}/encrypt'
        
        payload = encrypt_room.dict(exclude_unset=True)
            
        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Encrypting room failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Encrypted room.")
        return Node(**res.json())

    # get node comfor given node id
    @validate_arguments
    async def get_room_groups(self, room_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None, raise_on_err: bool = False) -> RoomGroupList:
        """ list (all) groups assigned to a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + \
            f'/rooms/{str(room_id)}/groups/?offset={str(offset)}'
        
        if filter: filter = urllib.parse.quote(filter)

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting room groups failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved room groups.")
        return RoomGroupList(**res.json())


    @validate_arguments
    async def update_room_groups(self, room_id: int, groups_update: UpdateRoomGroups, raise_on_err: bool = False) -> None:
        """ bulk update assigned groups of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(room_id)}/groups'

        payload = groups_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating room groups failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Updated room groups.")
        return None

    # delete groups assigned to room with given node id
    @validate_arguments
    async def delete_room_groups(self, room_id: int, group_list: List[int], raise_on_err: bool = False) -> None:
        """ bulk delete assigned groups of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "ids": group_list
        }
        api_url = self.api_url + f'/rooms/{str(room_id)}/groups'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting room groups failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Deleted room group(s).")
        return None

    # get node comfor given node id

    @validate_arguments
    async def get_room_users(self, room_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None, raise_on_err: bool = False) -> RoomUserList:
        """ get (all) users assigned to a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
            
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + \
            f'/rooms/{str(room_id)}/users/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting room users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Retrieved room users.")
        return RoomUserList(**res.json())

    # add or change users assigned to room with given node id
    @validate_arguments
    async def update_room_users(self, room_id: int, users_update: UpdateRoomUsers, raise_on_err: bool = False) -> None:
        """ bulk update assigned users in a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(room_id)}/users'

        payload = users_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating room users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Updated room user(s).")
        return None

    # delete users assigned to room with given node id
    @validate_arguments
    async def delete_room_users(self, room_id: int, user_list: List[int], raise_on_err: bool = False) -> None:
        """ bulk remove assigned users in a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = {
            "ids": user_list
        }

        api_url = self.api_url + f'/rooms/{str(room_id)}/users'
        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting room users failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Deleted room user(s).")
        return None

    # get webhooks assigned or assignable to room with given node id
    @validate_arguments
    async def get_room_webhooks(self, node_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None, raise_on_err: bool = False) -> RoomWebhookList:
        """" list (all) room webhooks """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + \
            f'/rooms/{str(node_id)}/webhooks/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting room webhooks failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Retrieved room webhooks.")
        return RoomWebhookList(**res.json())

    # delete users assigned to room with given node id

    @validate_arguments
    async def update_room_webhooks(self, node_id: int, hook_update: UpdateRoomHooks, raise_on_err: bool = False) -> RoomWebhookList:
        """ update room webhooks """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/{str(node_id)}/webhooks'

        payload = hook_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating room webhooks failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Updated room webhooks.")
        return RoomWebhookList(**res.json())
    
    @validate_arguments
    async def get_room_events(self, room_id: int, offset: int = 0, filter: str = None, limit: int = None, 
                        sort: str = None, date_start: str = None, date_end: str = None, operation_id: int = None, user_id: int = None, raise_on_err = False) -> LogEventList:
        """ get pending room assignments (new group members not accepted) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
            
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/rooms/{room_id}/events/?offset={str(offset)}'

        if date_start != None: api_url += f'&date_start={date_start}'
        if date_end != None: api_url += f'&date_end={date_end}'
        if operation_id != None: api_url += f'&type={str(operation_id)}'
        if user_id != None: api_url += f'&user_id={str(user_id)}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting room events failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved room events.")
        return LogEventList(**res.json())

    
    @validate_arguments
    async def get_pending_assignments(self, offset: int = 0, filter: str = None, limit: str = None, sort: str = None, raise_on_err: bool = False) -> PendingAssignmentList:
        """ get pending room assignments (new group members not accepted) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/pending/?offset={str(offset)}'
        
        if filter: filter = urllib.parse.quote(filter)

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting pending assingments failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved pending assignments.")
        return PendingAssignmentList(**res.json())


    @validate_arguments
    async def process_pending_assignments(self, pending_update: ProcessRoomPendingUsers, raise_on_err: bool = False) -> None:
        """ procces (accept or reject) new group members of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/rooms/pending'

        payload = pending_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Processing pending assingments failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Processed pending assignments.")
        return None

    # search for nodes
    @validate_arguments
    async def search_nodes(self, search: str, parent_id: int = 0, depth_level: int = 0, offset: int = 0, 
                           filter: str = None, limit: str = None, sort: str = None, raise_on_err: bool = False) -> NodeList:
        """ search for specific nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
            
        search = urllib.parse.quote(search)
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + \
            f'/search/?search_string={search}&offset={str(offset)}&parent_id={str(parent_id)}&depth_level={depth_level}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Searching nodes failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

        self.logger.info("Retrieved node(s) from search.")
        return NodeList(**res.json())