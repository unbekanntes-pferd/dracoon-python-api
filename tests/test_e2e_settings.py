import os
import asyncio
import unittest
import dotenv
from dracoon import DRACOONClient, OAuth2ConnectionType
from dracoon.nodes.responses import Webhook
from dracoon.settings import DRACOONSettings
from dracoon.settings.models import CreateWebhook, UpdateSettings, UpdateWebhook
from dracoon.settings.responses import CustomerSettingsResponse, EventTypeList, WebhookList


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')

class TestAsyncDRACOONPublic(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.settings = DRACOONSettings(dracoon_client=self.dracoon)
        assert isinstance(self.settings, DRACOONSettings)
        
    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_settings(self):
        customer_settings = await self.settings.get_settings()
        assert isinstance(customer_settings, CustomerSettingsResponse)
        
    async def test_update_settings(self):
        customer_settings_update = self.settings.make_settings_update(home_room_quota=1000000)
        assert isinstance(customer_settings_update, UpdateSettings)
        customer_settings_req = await self.settings.update_settings(settings_update=customer_settings_update)
        assert isinstance(customer_settings_req, CustomerSettingsResponse)
        
    async def test_get_webhooks(self):
        customer_webhooks = await self.settings.get_webhooks()
        assert isinstance(customer_webhooks, WebhookList)
    
    async def test_create_webhook(self):
        webhook_payload = self.settings.make_webhook(name='CREATE TEST', event_types=["file.created"], url="https://hooks.unbekanntespferd.com/test", trigger_example=False)
        assert isinstance(webhook_payload, CreateWebhook)
        webhook = await self.settings.create_webhook(hook=webhook_payload)
        assert isinstance(webhook, Webhook)
        await self.settings.delete_webhook(hook_id=webhook.id)

    async def test_update_webhook(self):
        
        webhook_payload = self.settings.make_webhook(name='UPDATE TEST', event_types=["file.created"], url="https://hooks.unbekanntespferd.com/test", trigger_example=False)
        assert isinstance(webhook_payload, CreateWebhook)
        webhook = await self.settings.create_webhook(hook=webhook_payload)
        assert isinstance(webhook, Webhook)
        
        update_name = 'UPDATED 2 TEST'
        
        webhook_update_payload = self.settings.make_webhook_update(name=update_name)
        assert isinstance(webhook_update_payload, UpdateWebhook)
        webhook_updated = await self.settings.update_webhook(hook_id=webhook.id, hook_update=webhook_update_payload)
        assert isinstance(webhook_updated, Webhook)
        assert webhook_updated.name == update_name
        
        await self.settings.delete_webhook(hook_id=webhook.id)

    
    async def test_delete_webhook(self):
        webhook_payload = self.settings.make_webhook(name='DELETE TEST', event_types=["file.created"], url="https://hooks.unbekanntespferd.com/test", trigger_example=False)
        assert isinstance(webhook_payload, CreateWebhook)
        webhook = await self.settings.create_webhook(hook=webhook_payload)
        assert isinstance(webhook, Webhook)
        
        del_webhook = await self.settings.delete_webhook(hook_id=webhook.id)
        assert del_webhook == None
    
    async def test_get_webhook_eventtypes(self):
        event_types = await self.settings.get_webhook_event_types()
        assert isinstance(event_types, EventTypeList)


if __name__ == '__main__':
    unittest.main()


   


