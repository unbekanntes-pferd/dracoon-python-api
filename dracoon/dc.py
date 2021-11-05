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

from dracoon.core import DRACOONClient, OAuth2ConnectionType
from dracoon.eventlog import DRACOONEvents
from dracoon.nodes import DRACOONNodes
from dracoon.shares import DRACOONShares

from .user import DRACOONUser
from .users import DRACOONUsers
from .groups import DRACOONGroups
from .uploads import DRACOONUploads
from .settings import DRACOONSettings
from .reports import DRACOONReports
from .crypto import decrypt_private_key

class DRACOON: 

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = ''):
        self.client = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

    async def connect(self, connection_type: OAuth2ConnectionType = OAuth2ConnectionType.auth_code, username: str = None, password: str = None):
        connection = await self.client.connect(connection_type=connection_type, username=username, password=password)

        self.nodes = DRACOONNodes(self.client)
        self.users = DRACOONUsers(self.client)
        self.user = DRACOONUser(self.client)
        self.groups = DRACOONGroups(self.client)
        self.settings = DRACOONSettings(self.client)
        self.uploads = DRACOONUploads(self.client)
        self.reports = DRACOONReports(self.client)
        self.shares = DRACOONShares(self.client)
        self.eventlog = DRACOONEvents(self.client)

    async def logout(self) -> None:
        await self.client.logout()

    async def test_connection(self) -> bool:
        return await self.client.test_connection()
    
    def valid_access_token(self) -> bool:
        return self.client.check_access_token()
    
    def valid_refresh_token(self) -> bool:
        return self.client.check_refresh_token()

    async def get_keypair(self, secret: str):
        if not self.client.connection:
            raise ValueError('DRACOON client not connected.')

        res = await self.user.get_user_keypair()
        enc_keypair = res.json()

        try:
            plain_keypair = decrypt_private_key(secret, enc_keypair)
        except:
            pass

        self.plain_keypair = plain_keypair

        return plain_keypair

    async def upload(self, file_path: str, target_path: str, options = None):
        if not self.client.connection:
            raise ValueError('DRACOON client not connected.')
        
        pass