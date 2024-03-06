
import os
import asyncio
from pathlib import Path
import unittest
import dotenv
from dracoon.branding.responses import CacheableBrandingResponse, ImageSize, ImageType, UpdateBrandingResponse, Upload

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.branding import DRACOONBranding, DRACOONPublicBranding

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')


class TestAsyncDRACOONBranding(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
        
        self.public_dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)

        self.branding = DRACOONBranding(dracoon_client=self.dracoon)
        self.public_branding = DRACOONPublicBranding(dracoon_client=self.public_dracoon)
        self.assertIsInstance(self.branding, DRACOONBranding)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        await self.public_dracoon.disconnect()
    
    async def test_get_branding(self):
        branding = await self.branding.get_branding()
        self.assertIsInstance(branding, UpdateBrandingResponse)

    async def test_update_branding(self):
        branding = await self.branding.get_branding()
        self.assertNotEqual(branding.emailContact, 'foo@unbekanntespferd.com')
        
        payload = self.branding.make_updateable_branding(branding=branding)
        payload = self.branding.make_branding_meta_update(branding=payload, product_name='TEST', email_contact='foo@unbekanntespferd.com')
        self.assertEqual(payload.emailContact, 'foo@unbekanntespferd.com')
        branding_update = await self.branding.update_branding(branding_update=payload)
        self.assertEqual(branding_update.emailContact, 'foo@unbekanntespferd.com')
        self.assertEqual(branding_update.productName, 'TEST')
        payload.emailContact = branding.emailContact
        payload.productName = branding.productName
        await self.branding.update_branding(branding_update=payload)
        
    async def test_upload_branding_image(self):
        image_bytes, _ = await self.public_branding.get_public_branding_image(type=ImageType.SQUARED_LOGO, size=ImageSize.LARGE)
        
        with open('test_branding.png', 'wb') as f:
            f.write(image_bytes)
            
        upload = await self.branding.upload_branding_image(type=ImageType.SQUARED_LOGO, file_path='test_branding.png')
        self.assertIsInstance(upload, Upload)
        
        path = Path('test_branding.png')
        
        os.remove(path)

    async def test_get_public_branding(self):
        public_branding = await self.public_branding.get_public_branding()
        self.assertIsInstance(public_branding, CacheableBrandingResponse)

    async def test_get_public_branding_image(self):
        
        image_bytes, content_type = await self.public_branding.get_public_branding_image(type=ImageType.SQUARED_LOGO, size=ImageSize.LARGE)
        
        with open('test_branding.png', 'wb') as f:
            f.write(image_bytes)
            
        path = Path('test_branding.png')
        self.assertIsNotNone(content_type)
        self.assertTrue(path.exists())
        self.assertTrue(path.is_file())
        os.remove(path)
