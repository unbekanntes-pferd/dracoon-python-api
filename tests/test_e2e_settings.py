
from dracoon.nodes.responses import Webhook
from dracoon.settings import DRACOONSettings
from dracoon import DRACOONClient, OAuth2ConnectionType
import dotenv
import os
import asyncio
from dracoon.settings.models import CreateWebhook, UpdateSettings, UpdateWebhook

from dracoon.settings.responses import CustomerSettingsResponse, EventTypeList, WebhookList


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

async def test_settings_e2e():

    dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    settings = DRACOONSettings(dracoon_client=dracoon)
    assert isinstance(settings, DRACOONSettings)
    print('Connection test complete (/)')

    customer_settings = await settings.get_settings()
    assert isinstance(customer_settings, CustomerSettingsResponse)
    print('Getting customer settings test passed (/)')

    customer_settings_update = settings.make_settings_update(home_room_quota=1000000)
    assert isinstance(customer_settings_update, UpdateSettings)
    print('Creating customer settings payload test passed (/)')

    customer_settings_req = await settings.update_settings(settings_update=customer_settings_update)
    assert isinstance(customer_settings_req, CustomerSettingsResponse)
    print('Updating customer settings test passed (/)')

    customer_webhooks = await settings.get_webhooks()
    assert isinstance(customer_webhooks, WebhookList)
    print('Getting customer webhooks test passed (/)')

    webhook_payload = settings.make_webhook(name='THIS IS A TEST', event_types=["file.created"], url="https://hooks.unbekanntespferd.com/test", trigger_example=False)
    assert isinstance(webhook_payload, CreateWebhook)
    print('Creating webhook creation payload test passed (/)')

    webhook = await settings.create_webhook(hook=webhook_payload)
    assert isinstance(webhook, Webhook)
    print('Creating webhook test passed (/)')

    webhook_update_payload = settings.make_webhook_update(name='THIS IS ANOTHER TEST')
    assert isinstance(webhook_update_payload, UpdateWebhook)
    print('Creating webhook creation payload test passed (/)')

    webhook_updated = await settings.update_webhook(hook_id=webhook.id, hook_update=webhook_update_payload)
    assert isinstance(webhook_updated, Webhook)
    assert webhook_updated.name == 'THIS IS ANOTHER TEST'
    print('Updating webhook test passed (/)')

    del_webhook = await settings.delete_webhook(hook_id=webhook.id)
    assert del_webhook == None
    print('Deleting webhook test passed (/)')

    event_types = await settings.get_webhook_event_types()
    assert isinstance(event_types, EventTypeList)
    print('Getting webhook event types test passed (/)')

    print('Settings E2E tests passed (/)')


if __name__ == '__main__':
    asyncio.run(test_settings_e2e())

    

   


