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

from .crypto_models import PlainUserKeyPairContainer
from .downloads import DRACOONDownloads
from .public import DRACOONPublic
from .public_models import ActiveDirectoryInfo, OpenIdInfo, SystemInfo
from .user_models import UserAccount
from .core import DRACOONClient, OAuth2ConnectionType
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
import asyncio

class DRACOON:
    """ DRACOON main API wrapper with all adapters to specific endpoints """ 

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = ''):
        """ intialize with instance information: base DRACOON url and OAuth app client credentials """
        self.client = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

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

        asyncio.gather()

        res = await self.user.get_account_information()
        self.user_info: UserAccount = res.json()

        res = await self.public.get_system_info()
        self.system_info: SystemInfo = res.json()

        res = await self.public.get_auth_openid_info()
        self.openid_info: OpenIdInfo = res.json()

        res = await self.public.get_auth_ad_info()
        self.ad_info: ActiveDirectoryInfo = res.json()

    async def logout(self, revoke_refresh_token: bool = False) -> None:
        """ closes the httpx client and revokes tokens """
        await self.client.logout(revoke_refresh_token=revoke_refresh_token)

    async def test_connection(self) -> bool:
        """ test authenticated connection via authenticated ping """
        return await self.client.test_connection()
    
    def valid_access_token(self) -> bool:
        """ check access token validity based on expiration """
        return self.client.check_access_token()
    
    def valid_refresh_token(self) -> bool:
        """ check refresh token validity based on expiration """
        return self.client.check_refresh_token()

    def check_keypair(self) -> bool:
        return self.plain_keypair is not None and self.user_info is not None

    async def get_keypair(self, secret: str) -> PlainUserKeyPairContainer:
        """ get user keypair """
        if not self.client.connection:
            raise ValueError('DRACOON client not connected.')

        res = await self.user.get_user_keypair()
        enc_keypair = res.json()

        
        plain_keypair = decrypt_private_key(secret, enc_keypair)

        self.plain_keypair = plain_keypair

        return plain_keypair

    async def upload(self, file_path: str, target_path: str, options = None):
        """ upload a file to a target """
        if not self.client.connection:
            raise ValueError('DRACOON client not connected.')

        node_info = await self.nodes.get_node_from_path(target_path)
        file_name = file_path.split('/')[-1]

        target_id = node_info["id"]
        is_encrypted = node_info["isEncrypted"]

        user_id = self.user_info["id"]

        upload_channel = self.nodes.make_upload_channel(target_id, file_name)
        res = await self.nodes.create_upload_channel(upload_channel)


        if is_encrypted and self.check_keypair():       
            upload = await self.uploads.upload_encrypted(file_path=file_path, user_id=user_id, upload_channel=res.json(), plain_keypair=self.plain_keypair)
        elif is_encrypted and not self.check_keypair():
            raise ValueError('DRACOON crypto upload requires unlocked keypair. Please unlock keypair first.')
        elif not is_encrypted:
            upload = await self.uploads.upload_unencrypted(file_path=file_path, upload_channel=res.json())

    async def download(self, file_path: str, target_path: str):
        """ download a file to a target """

        if not self.client.connection:
            raise ValueError('DRACOON client not connected.')

        node_info = await self.nodes.get_node_from_path(file_path)
        node_id = node_info["id"]

        is_encrypted = node_info["isEncrypted"]

        res = await self.nodes.get_download_url(node_id=node_id)

        download_url = res.json()["downloadUrl"]

        if not is_encrypted:
            await self.downloads.download_unencrypted(download_url=download_url, target_path=target_path, node_info=node_info)
        elif is_encrypted and self.check_keypair():
            file_key = await self.nodes.get_user_file_key(node_id)
            await self.downloads.download_encrypted(download_url=download_url, target_path=target_path, node_info=node_info, plain_keypair=self.plain_keypair, file_key=file_key.json())


    def get_code_url(self) -> str:
        """ get code url for authorization code flow """
        return self.client.get_code_url()