"""
Async DRACOON API wrapper based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls
Documentation: https://dracoon.team/api

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 
All requests with bodies use generic params variable to pass JSON body

"""

from .crypto.models import PlainUserKeyPairContainer
from .downloads import DRACOONDownloads
from .public import DRACOONPublic
from .client import DRACOONClient, OAuth2ConnectionType
from .eventlog import DRACOONEvents
from .nodes import DRACOONNodes
from .shares import DRACOONShares
from .user import DRACOONUser
from .users import DRACOONUsers
from .groups import DRACOONGroups
from .uploads import DRACOONUploads
from .settings import DRACOONSettings
from .reports import DRACOONReports
from .crypto import decrypt_private_key
from .logger import create_logger
import asyncio
import logging


class DRACOON:
    """ DRACOON main API wrapper with all adapters to specific endpoints """ 

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = '', log_file: str = 'dracoon.log', log_level = logging.INFO, log_stream: bool = False):
        """ intialize with instance information: base DRACOON url and OAuth app client credentials """
        self.client = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        self.logger = create_logger(log_file=log_file, log_level=log_level, log_stream=log_stream)
        self.logger.info("Created DRACOON client.")
        self.plain_keypair = None
        self.user_info =  None


    async def connect(self, connection_type: OAuth2ConnectionType = OAuth2ConnectionType.auth_code, username: str = None, password: str = None, auth_code = None):
        """ establishes a connection required for all adapters """
        connection = await self.client.connect(connection_type=connection_type, username=username, password=password, auth_code=auth_code)

        self.nodes = DRACOONNodes(self.client)
        self.users = DRACOONUsers(self.client)
        self.user = DRACOONUser(self.client)
        self.groups = DRACOONGroups(self.client)
        self.settings = DRACOONSettings(self.client)
        self.uploads = DRACOONUploads(self.client)
        self.downloads = DRACOONDownloads(self.client)
        self.reports = DRACOONReports(self.client)
        self.shares = DRACOONShares(self.client)
        self.eventlog = DRACOONEvents(self.client)
        self.public = DRACOONPublic(self.client)

        self.logger.info("Initialized DRACOON adapters.") 

        user_info_res = self.user.get_account_information()
        system_info_res = self.public.get_system_info()
        oidc_auth_info_res = self.public.get_auth_openid_info()
        ad_auth_info_res = self.public.get_auth_ad_info()

        self.logger.debug("Getting DRACOON instance information...")

        list = await asyncio.gather(user_info_res, system_info_res, oidc_auth_info_res, ad_auth_info_res)
        
        self.user_info = list[0]
        self.system_info = list[1]
        self.auth_ad_info = list[3]
        self.auth_oidc_info = list[2]

        self.logger.info("Retrieved instance and account information.")
        self.logger.debug("Logged in as user id %s.", self.user_info.id)
        self.logger.debug("Using S3: %s.", self.system_info.useS3Storage)
        
    async def logout(self, revoke_refresh_token: bool = False) -> None:
        """ closes the httpx client and revokes tokens """
        await self.client.logout(revoke_refresh_token=revoke_refresh_token)
        self.logger.info("Revoked token(s).")
        self.logger.debug("Refresh token revoked: %s", revoke_refresh_token)

    async def test_connection(self) -> bool:
        """ test authenticated connection via authenticated ping """
        self.logger.debug("Testing authenticated connection.")
        return await self.client.test_connection()
    
    def valid_access_token(self) -> bool:
        """ check access token validity based on expiration """
        self.logger.debug("Checking access token validity.")
        return self.client.check_access_token()
    
    def valid_refresh_token(self) -> bool:
        """ check refresh token validity based on expiration """
        self.logger.debug("Checking refresh token validity.")
        return self.client.check_refresh_token()

    def check_keypair(self) -> bool:
        
        if not self.plain_keypair:
            return False
        
        self.logger.info("Checking user keypair.")
        return self.plain_keypair is not None and self.user_info is not None

    async def get_keypair(self, secret: str) -> PlainUserKeyPairContainer:
        """ get user keypair """
        if not self.client.connection:
            self.logger.error("DRACOON client not connected: Keypair not retrieved.")
            raise ValueError('DRACOON client not connected.')

        enc_keypair = await self.user.get_user_keypair()
      
        plain_keypair = decrypt_private_key(secret, enc_keypair)

        self.plain_keypair = plain_keypair

        self.logger.info("Retrieved user keypair.")
        self.logger.debug("User keypair version: %s", self.plain_keypair.publicKeyContainer.version)

        return plain_keypair

    async def upload(self, file_path: str, target_path: str, display_progress: bool = False):
        """ upload a file to a target """
        if not self.client.connection:
            self.logger.error("DRACOON client not connected: Upload failed.")
            raise ValueError('DRACOON client not connected.')

        node_info = await self.nodes.get_node_from_path(target_path)
        
        if not node_info:
            self.logger.critical('Upload failed: Invalid target path.')
            self.logger.debug('Node %s not found.', target_path)
            raise ValueError('Node %s not found.', target_path)
        
        file_name = file_path.split('/')[-1]
        
        self.logger.info("Uploading file.")
        self.logger.debug("File: %s", file_path)
        self.logger.debug("Destination: %s", target_path)

        target_id = node_info.id
        is_encrypted = node_info.isEncrypted

        self.logger.debug("Encrypted: %s", is_encrypted)

        user_id = self.user_info.id
        
        use_s3_storage = False
        
        if self.system_info.useS3Storage:
            use_s3_storage = True
    
        self.logger.debug("Using S3 storage: %s", use_s3_storage)
            
        upload_channel_payload = self.nodes.make_upload_channel(parent_id=target_id, name=file_name, direct_s3_upload=use_s3_storage)
        upload_channel = await self.nodes.create_upload_channel(upload_channel_payload)
    

        self.logger.debug("Created upload channel: %s", upload_channel.uploadId)
        self.logger.debug("Upload URL (redacted): %s", upload_channel.uploadUrl[:-4])

        # crypto upload 
        if is_encrypted and self.check_keypair() and not use_s3_storage:       
            upload = await self.uploads.upload_encrypted(file_path=file_path, user_id=user_id, upload_channel=upload_channel, plain_keypair=self.plain_keypair)
        elif is_encrypted and self.check_keypair() and use_s3_storage:
            upload = await self.nodes.upload_s3_encrypted(file_path=file_path, upload_channel=upload_channel, plain_keypair=self.plain_keypair, display_progress=display_progress)
        elif is_encrypted and not self.check_keypair():
            self.logger.critical("Upload failed: Keypair not unlocked.")
            raise ValueError('DRACOON crypto upload requires unlocked keypair. Please unlock keypair first.')
        # unencrypted upload
        elif not is_encrypted and not use_s3_storage:
            upload = await self.uploads.upload_unencrypted(file_path=file_path, upload_channel=upload_channel)
        elif not is_encrypted and use_s3_storage:
            upload = await self.nodes.upload_s3_unencrypted(file_path=file_path, upload_channel=upload_channel, display_progress=display_progress)

        self.logger.info("Upload completed.")
        
        if upload: return upload

    async def download(self, file_path: str, target_path: str, display_progress: bool = False):
        """ download a file to a target """

        if not self.client.connection:
            await self.client.http.aclose()
            self.logger.error("DRACOON client not connected: Download failed.")
            raise ValueError('DRACOON client not connected.')

        node_info = await self.nodes.get_node_from_path(file_path)
        
        if not node_info:
            self.logger.error("Download failed: file does not exist.")
            self.logger.debug("File %s not found", file_path)
            await self.client.http.aclose()
            raise ValueError('File does not exist.')
        
        node_id = node_info.id

        is_encrypted = node_info.isEncrypted

        self.logger.info("Downloading file.")
        self.logger.debug("File: %s", file_path)
        self.logger.debug("Destination: %s", target_path)
        self.logger.debug("Encrypted: %s", is_encrypted)

        dl_token_res = await self.nodes.get_download_url(node_id=node_id)

        download_url = dl_token_res.downloadUrl

        self.logger.debug("Download URL (redacted): %s", download_url[:-4])

        if not is_encrypted:
            await self.downloads.download_unencrypted(download_url=download_url, target_path=target_path, node_info=node_info, display_progress=display_progress)
        elif is_encrypted and self.check_keypair():
            file_key = await self.nodes.get_user_file_key(node_id)
            await self.downloads.download_encrypted(download_url=download_url, target_path=target_path, node_info=node_info, plain_keypair=self.plain_keypair, file_key=file_key, display_progress=display_progress)
        elif is_encrypted and not self.check_keypair():
            raise ValueError('Keypair must be entered for encrypted nodes.')


    def get_code_url(self) -> str:
        """ get code url for authorization code flow """
        self.logger.info("Getting authorization URL.")
        return self.client.get_code_url()