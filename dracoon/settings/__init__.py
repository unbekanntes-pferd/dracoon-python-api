"""
Async DRACOON settings adapter based on httpx and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for settings (Webhooks)
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/groups
Webhooks documentation: https://support.dracoon.com/hc/de/articles/360013167959-Webhooks 
Please note: maximum 500 items are returned in GET requests
 - refer to documentation for details on filtering and offset
 - use documentation for payload description

"""

from typing import List, Optional
import logging
import urllib.parse

from dracoon.client import DRACOONClient
from dracoon.errors import InvalidArgumentError, InvalidClientError, ClientDisconnectedError
from .models import CreateWebhook, UpdateSettings, UpdateWebhook
from .responses import EventTypeList, WebhookList, Webhook, CustomerSettingsResponse

class DRACOONSettings:

    """
    API wrapper for DRACOON settings endpoint:
    Settings an webhooks management – config manager role required
    """
    
    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')

        self.logger = logging.getLogger('dracoon.settings')
         
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/settings'

            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    async def get_settings(self, raise_on_err: bool = False) -> Optional[CustomerSettingsResponse]:
        """ list customer settings (home rooms) """
        if self.raise_on_err:
            raise_on_err = True

        res = await self.dracoon.request('GET', self.api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting settings failed.")
            return None
        
        self.logger.info("Retrieved customer settings.")
        return CustomerSettingsResponse(**res.json())

    async def update_settings(self, settings_update: UpdateSettings, raise_on_err: bool = False) -> Optional[CustomerSettingsResponse]:
        """ update customer settings (home rooms) """
        if self.raise_on_err:
            raise_on_err = True

        payload = settings_update.model_dump(exclude_unset=True)

        res = await self.dracoon.request('PUT', url=self.api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating settings failed.")
            return None
        
        self.logger.info("Updated customer settings.")
        return CustomerSettingsResponse(**res.json())
    
    def make_settings_update(self, home_rooms_active: bool = None, home_room_quota: int = None, home_room_parent_name: str = None, raise_on_err: bool = False) -> UpdateSettings:
        """ make a settings update payload required for update_settings() """
        settings_update = {}

        if home_rooms_active == False:
            raise InvalidArgumentError(message='Home rooms cannot be deactivated')

        if home_rooms_active is not None: settings_update["homeRoomsActive"] = home_rooms_active
        if home_room_quota: settings_update["homeRoomQuota"] = home_room_quota
        if home_room_parent_name: settings_update["homeRoomParentName"] = home_room_parent_name

        return UpdateSettings(**settings_update)

    async def get_webhooks(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> Optional[WebhookList]:
        """ list (all) webhooks """
        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/webhooks?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting webhooks failed.")
            return None
        
        self.logger.info("Retrieved webhooks.")
        return WebhookList(**res.json())


    async def create_webhook(self, hook: CreateWebhook, raise_on_err: bool = False) -> Optional[Webhook]:
        """ creates a new webhook """
        payload = hook.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + '/webhooks'
        res = await self.dracoon.request('POST', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Creating webhook failed.")
            return None
        
        self.logger.info("Created webhook.")
        return Webhook(**res.json())

    def make_webhook(self, name: str, event_types: List[str], url: str, secret: str = None, 
                     is_enabled: bool = None, trigger_example: bool = None) -> CreateWebhook:
        """ make a new webhook creation payload required for create_webhook() """
        webhook = {
            "name": name,
            "eventTypeNames": event_types,
            "url": url
        }
        
        if secret: webhook["secret"] = secret
        if is_enabled is not None: webhook["isEnabled"] = is_enabled
        if trigger_example is not None: webhook["triggerExampleEvent"] = trigger_example

        return CreateWebhook(**webhook)

    def make_webhook_update(self, name: str = None, event_types: List[str] = None, url: str = None, secret: str = None, 
                     is_enabled: bool = None, trigger_example: bool = None) -> UpdateWebhook:
        """ make a new webhook update payload required for update_webhook() """
        webhook = {}
        
        if name: webhook["name"] = name
        if event_types: webhook["eventTypeNames"] = event_types
        if url: webhook["url"] = url
        if secret: webhook["secret"] = secret
        if is_enabled is not None: webhook["isEnabled"] = is_enabled
        if trigger_example is not None: webhook["triggerExampleEvent"] = trigger_example

        return UpdateWebhook(**webhook)


    async def get_webhook(self, hook_id: int, raise_on_err: bool = False) -> Optional[Webhook]:
        """ get webhook details for specific user (by id) """
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting webhook failed.")
            return None
        
        self.logger.info("Retrieved webhook.")
        return Webhook(**res.json())

    async def update_webhook(self, hook_id: int, hook_update: UpdateWebhook, raise_on_err: bool = False) -> Optional[Webhook]:

        payload = hook_update.model_dump(exclude_unset=True)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        res = await self.dracoon.request('PUT', api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating webhook failed.")
            return None
        
        self.logger.info("Updated webhook.")
        return Webhook(**res.json())


    async def delete_webhook(self, hook_id: int, raise_on_err: bool = False) -> None:
        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        res = await self.dracoon.request('DELETE', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Deleting webhook failed.")
            return None
        self.logger.info("Deleted webhook.")
        return None
    
    async def get_webhook_event_types(self, raise_on_err: bool = False) -> Optional[EventTypeList]:

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + '/webhooks/event_types'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting webhook event types failed.")
            return None
        
        self.logger.info("Retrieved webhook event types.")
        return EventTypeList(**res.json())