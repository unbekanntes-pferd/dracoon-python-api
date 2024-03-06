import os
import asyncio
import unittest

import dotenv

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.eventlog import DRACOONEvents
from dracoon.eventlog.responses import AuditNodeInfoResponse, AuditNodeResponse, LogEventList

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')

class TestAsyncDRACOONEventlog(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.eventlog = DRACOONEvents(dracoon_client=self.dracoon)
        self.assertIsInstance(self.eventlog, DRACOONEvents)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_permissions(self):
        permissions_audit = await self.eventlog.get_permissions()
        self.assertGreater(len(permissions_audit), 0)
        self.assertIsInstance(permissions_audit[0], AuditNodeResponse)

    async def test_get_events(self):
        events_audit = await self.eventlog.get_events()
        self.assertIsInstance(events_audit, LogEventList)
    
    async def test_get_rooms(self):
        room_list = await self.eventlog.get_rooms()
        self.assertIsInstance(room_list, AuditNodeInfoResponse)

if __name__ == '__main__':
    unittest.main()