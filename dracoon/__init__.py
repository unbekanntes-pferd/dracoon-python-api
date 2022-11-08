"""
Async DRACOON API wrapper based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls
Documentation: https://dracoon.team/api

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 
All requests with bodies use generic params variable to pass JSON body

"""


import logging
import asyncio
from pathlib import Path
from typing import Any, Generator, List
from datetime import datetime
from dracoon.branding import DRACOONBranding
from dracoon.client.models import ProxyConfig
from dracoon.config import DRACOONConfig
from dracoon.config.responses import GeneralSettingsInfo, InfrastructureProperties, SystemDefaults
from dracoon.nodes.models import Callback
from dracoon.nodes.responses import S3FileUploadStatus
from dracoon.public.responses import AuthADInfo, AuthOIDCInfo, SystemInfo
from dracoon.user.models import UserAccount

from .crypto.models import PlainUserKeyPairContainer
from .downloads import DRACOONDownloads
from .public import DRACOONPublic
from .client import DRACOONClient, DRACOONConnection, OAuth2ConnectionType
from .eventlog import DRACOONEvents
from .nodes import CHUNK_SIZE, MIN_CHUNK_SIZE, DRACOONNodes
from .shares import DRACOONShares
from .user import DRACOONUser
from .users import DRACOONUsers
from .groups import DRACOONGroups
from .settings import DRACOONSettings
from .reports import DRACOONReports
from .crypto import decrypt_private_key
from .logger import create_logger
from .errors import (CryptoMissingFileKeyError, CryptoMissingKeypairError, DRACOONCryptoError,
                     HTTPNotFoundError, InvalidArgumentError, InvalidFileError, InvalidPathError, ClientDisconnectedError)



class DRACOON:
    """ DRACOON main API wrapper with all adapters to specific endpoints """ 

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = '', redirect_uri: str = None,
                 log_file: str = 'dracoon.log', log_level = logging.INFO, log_stream: bool = False, raise_on_err: bool = False, 
                 proxy_config: ProxyConfig = None, log_file_out: bool = False):
        """ intialize with instance information: base DRACOON url and OAuth app client credentials """
        self.client = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=raise_on_err, 
                                    proxy_config=proxy_config, redirect_uri=redirect_uri)
        self.logger = create_logger(log_file=log_file, log_level=log_level, log_stream=log_stream, log_file_out=log_file_out)
        self.logger.info("Created DRACOON client.")
        self.plain_keypair = None
        self.user_info =  None
        
    @property
    def config(self) -> DRACOONConfig:
        return DRACOONConfig(self.client)
  
    @property 
    def nodes(self) -> DRACOONNodes:
        return DRACOONNodes(self.client)
    
    @property  
    def public(self) -> DRACOONPublic:
        return DRACOONPublic(self.client)
    
    @property 
    def user(self) -> DRACOONUser:
        return DRACOONUser(self.client)
    
    @property 
    def reports(self) -> DRACOONReports:
        return DRACOONReports(self.client)
    
    @property 
    def settings(self) -> DRACOONSettings:
        return DRACOONSettings(self.client)
    
    @property
    def users(self) -> DRACOONUsers:
       return DRACOONUsers(self.client) 
   
    @property 
    def groups(self) -> DRACOONGroups:
        return DRACOONGroups(self.client)
    
    @property 
    def eventlog(self) -> DRACOONEvents:
        return DRACOONEvents(self.client)
    
    @property
    def shares(self) -> DRACOONShares:
       return DRACOONShares(self.client) 
   
    @property
    def downloads(self) -> DRACOONDownloads:
       return DRACOONDownloads(self.client)

    @property
    def branding(self) -> DRACOONBranding:
       return DRACOONBranding(self.client) 
   
    async def connect(self, connection_type: OAuth2ConnectionType = OAuth2ConnectionType.auth_code, username: str = None, 
                      password: str = None, auth_code: str = None, refresh_token: str = None, redirect_uri: str = None) -> DRACOONConnection:
        """ establishes a connection required for all adapters """
        self.connection = await self.client.connect(connection_type=connection_type, username=username, password=password, 
                                               auth_code=auth_code, refresh_token=refresh_token, redirect_uri=redirect_uri)

        self.logger.info("Initialized DRACOON adapters.") 

        user_info_res = self.user.get_account_information()
        system_info_res = self.public.get_system_info()
        oidc_auth_info_res = self.public.get_auth_openid_info()
        ad_auth_info_res = self.public.get_auth_ad_info()
        
        system_defaults = self.config.get_system_defaults()
        infrastructure_policies = self.config.get_infrastructure_properties()
        general_settings = self.config.get_general_settings()

        self.logger.debug("Getting DRACOON instance information...")

        reqs = await asyncio.gather(user_info_res, system_info_res, oidc_auth_info_res, ad_auth_info_res, system_defaults, infrastructure_policies, general_settings)
        
        self.user_info: UserAccount = reqs[0]
        self.system_info: SystemInfo = reqs[1]
        self.auth_ad_info: AuthADInfo = reqs[3]
        self.auth_oidc_info: AuthOIDCInfo = reqs[2]
        self.general_settings: GeneralSettingsInfo = reqs[6]
        self.system_defaults: SystemDefaults = reqs[4]
        self.infrastructure_policies: InfrastructureProperties = reqs[5]

        self.logger.info("Retrieved instance and account information.")
        self.logger.debug("Logged in as user id %s.", self.user_info.id)
        self.logger.debug("Using S3: %s.", self.system_info.useS3Storage)
        
        return self.connection
        
    async def logout(self, revoke_refresh_token: bool = False) -> None:
        """ closes the httpx client and revokes tokens """
        await self.client.logout(revoke_refresh_token=revoke_refresh_token)
        self.logger.info("Revoked token(s).")
        self.logger.debug("Refresh token revoked: %s", revoke_refresh_token)

    async def test_connection(self) -> bool:
        """ test authenticated connection via authenticated ping """
        self.logger.debug("Testing authenticated connection.")
        return await self.client.test_connection()
    
    async def valid_access_token(self) -> bool:
        """ check access token validity based on expiration """
        self.logger.debug("Checking access token validity.")
        return self.client.check_access_token()
    
    def check_keypair(self) -> bool:
        
        if not self.plain_keypair:
            return False
        
        self.logger.info("Checking user keypair.")
        return self.plain_keypair is not None and self.user_info is not None

    async def get_keypair(self, secret: str) -> PlainUserKeyPairContainer:
        """ get user keypair """
        if not self.client.connection:
            self.logger.error("DRACOON client not connected: Keypair not retrieved.")
            raise ClientDisconnectedError()
        
        enc_keypair = await self.user.get_user_keypair(raise_on_err=True)
        try:
            plain_keypair = decrypt_private_key(secret, enc_keypair)
        except ValueError:
            raise DRACOONCryptoError(message="Wrong encryption password")
        except TypeError:
            raise DRACOONCryptoError(message="Encryption password must not be empty")

        self.plain_keypair = plain_keypair

        self.logger.info("Retrieved user keypair.")
        self.logger.debug("User keypair version: %s", self.plain_keypair.publicKeyContainer.version)

        return plain_keypair

    async def upload(self, file_path: str, target_path: str = None, file_name: str = None, resolution_strategy: str = 'autorename', 
                     display_progress: bool = False, modification_date: str = None, 
                     creation_date: str = None, 
                     raise_on_err: bool = False, callback_fn: Callback  = None,
                     target_parent_id: int = None,
                     chunksize: int = CHUNK_SIZE
                     ) -> S3FileUploadStatus:  
        """ upload a file to a target """
        if not self.client.connection:
            self.logger.error("DRACOON client not connected: Upload failed.")
            err = ClientDisconnectedError(message="DRACOON client not connected.")
            await self.client.handle_generic_error(err=err)
            
        if self.client.raise_on_err:
            raise_on_err = True
            
        if target_parent_id is None and target_path is None:
            self.logger.critical('Upload failed: Missing target info - id or path must be provided.')
            err = InvalidPathError(message='Missing mandatory arguments: target path or target parent id')
            await self.client.handle_generic_error(err=err)
            
            
        if target_parent_id is not None:
            node_info = await self.nodes.get_node(node_id=target_parent_id, raise_on_err=raise_on_err)
        elif target_path is not None:
            node_info = await self.nodes.get_node_from_path(path=target_path, raise_on_err=raise_on_err)
        else:
            raise InvalidArgumentError("Missing node info: Provide target path or node id.")
        
        if not node_info:
            self.logger.critical('Upload failed: Invalid target path.')
            msg = 'Node %s not found.', target_path
            self.logger.debug(msg)
            err = InvalidPathError(message=msg)
            await self.client.handle_generic_error(err=err)
            
        if file_name is None: 
            file_name = Path(file_path).name
            
        file_modified = Path(file_path).stat().st_mtime
        file_created = Path(file_path).stat().st_ctime
        
        if modification_date is None:
            modification_date = datetime.fromtimestamp(file_modified).strftime('%Y-%m-%dT%H:%M:%S')
            
        if creation_date is None:
            creation_date = datetime.fromtimestamp(file_created).strftime('%Y-%m-%dT%H:%M:%S')

           
        self.logger.info("Uploading file.")
        self.logger.debug("File: %s", file_path)
        self.logger.debug("Destination: %s", target_path)

        target_id = node_info.id
        is_encrypted = node_info.isEncrypted

        self.logger.debug("Encrypted: %s", is_encrypted)
        
        use_s3_storage = False
        
        if self.system_info.useS3Storage:
            use_s3_storage = True    
            if chunksize < MIN_CHUNK_SIZE: chunksize = MIN_CHUNK_SIZE

        self.logger.debug("Using S3 storage: %s", use_s3_storage)
            
        upload_channel_payload = self.nodes.make_upload_channel(parent_id=target_id, name=file_name, direct_s3_upload=use_s3_storage, 
                                                                modification_date=modification_date, creation_date=creation_date)
        upload_channel = await self.nodes.create_upload_channel(upload_channel=upload_channel_payload, raise_on_err=raise_on_err)
    

        self.logger.debug("Created upload channel: %s", upload_channel.uploadId)
        self.logger.debug("Upload URL (redacted): %s", upload_channel.uploadUrl[:-4])

        # crypto upload 
        if is_encrypted and self.check_keypair() and not use_s3_storage:       
            upload = await self.nodes.upload_encrypted(file_path=file_path, upload_channel=upload_channel, display_progress=display_progress,
                                                         plain_keypair=self.plain_keypair, resolution_strategy=resolution_strategy, file_name=file_name,
                                                         raise_on_err=raise_on_err, callback_fn=callback_fn, chunksize=chunksize)
        elif is_encrypted and self.check_keypair() and use_s3_storage:
            upload = await self.nodes.upload_s3_encrypted(file_path=file_path, upload_channel=upload_channel, plain_keypair=self.plain_keypair, 
                                                          display_progress=display_progress, resolution_strategy=resolution_strategy, file_name=file_name,
                                                          raise_on_err=raise_on_err, callback_fn=callback_fn, chunksize=chunksize)
        elif is_encrypted and not self.check_keypair():
            self.logger.critical("Upload failed: Keypair not unlocked.")
            raise CryptoMissingKeypairError('DRACOON crypto upload requires unlocked keypair. Please unlock keypair first.')
        # unencrypted upload
        elif not is_encrypted and not use_s3_storage:
            upload = await self.nodes.upload_unencrypted(file_path=file_path, upload_channel=upload_channel, file_name=file_name,
                                                         resolution_strategy=resolution_strategy, display_progress=display_progress, 
                                                         raise_on_err=raise_on_err, callback_fn=callback_fn, chunksize=chunksize)
        elif not is_encrypted and use_s3_storage:
            upload = await self.nodes.upload_s3_unencrypted(file_path=file_path, upload_channel=upload_channel, file_name=file_name,
                                                            display_progress=display_progress, resolution_strategy=resolution_strategy,
                                                            raise_on_err=raise_on_err, callback_fn=callback_fn, chunksize=chunksize)

        self.logger.info("Upload completed.")
        
        return upload

    async def download(self, target_path: str, file_path: str = None, display_progress: bool = False, raise_on_err: bool = False, 
                       callback_fn: Callback  = None, file_name: str = None, source_node_id: int = None, chunksize: int = CHUNK_SIZE):
        """ download a file to a target """

        if not self.client.connection:
            await self.client.disconnect()
            self.logger.error("DRACOON client not connected: Download failed.")
            raise ClientDisconnectedError(message='DRACOON client not connected.')

        if self.client.raise_on_err:
            raise_on_err = True
            
        if source_node_id is not None:
            node_id = source_node_id
            node_info = await self.nodes.get_node(node_id=node_id)   
        elif file_path is not None:
            node_info = await self.nodes.get_node_from_path(path=file_path, raise_on_err=raise_on_err)
        else:
            raise InvalidArgumentError("Missing node info: provide either id or file path")
        
        if not node_info:
            self.logger.error("Download failed: file does not exist.")
            self.logger.debug("File %s not found", file_path)
            err = InvalidFileError(message='File does not exist.')
            await self.client.handle_generic_error(err=err)
        
        node_id = node_info.id

        is_encrypted = node_info.isEncrypted

        self.logger.info("Downloading file.")
        self.logger.debug("File: %s", file_path)
        self.logger.debug("Destination: %s", target_path)
        self.logger.debug("Encrypted: %s", is_encrypted)

        dl_token_res = await self.nodes.get_download_url(node_id=node_id, raise_on_err=raise_on_err)

        download_url = dl_token_res.downloadUrl

        self.logger.debug("Download URL (redacted): %s", download_url[:-4])

        if not is_encrypted:
            await self.downloads.download_unencrypted(download_url=download_url, target_path=target_path, node_info=node_info, 
                                                      display_progress=display_progress, raise_on_err=raise_on_err, 
                                                      callback_fn=callback_fn, file_name=file_name, chunksize=chunksize)
        elif is_encrypted and self.check_keypair():
            try:
                file_key = await self.nodes.get_user_file_key(node_id, raise_on_err=True)
                await self.downloads.download_encrypted(download_url=download_url, target_path=target_path, node_info=node_info, 
                                                    plain_keypair=self.plain_keypair, file_key=file_key, display_progress=display_progress, 
                                                    raise_on_err=raise_on_err, callback_fn=callback_fn, file_name=file_name, chunksize=chunksize)
            except HTTPNotFoundError:
                raise CryptoMissingFileKeyError(message=f'No file key for node {node_id}')
                
        elif is_encrypted and not self.check_keypair():
            raise CryptoMissingKeypairError(message='Keypair must be entered for encrypted nodes.')


    def get_code_url(self) -> str:
        """ get code url for authorization code flow """
        self.logger.info("Getting authorization URL.")
        return self.client.get_code_url()

    def batch_process(self, coro_list: List[Any], batch_size: int = 5) -> Generator[Any, None, None]:
        """ 
        helper method which returns a generator for a list 
        of couroutines 
        utility to process multiple requests async
        """ 
        return (coro_list[i:i + batch_size]  for i in range(0, len(coro_list), batch_size))
