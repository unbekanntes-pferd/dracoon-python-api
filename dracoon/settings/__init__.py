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

from typing import List
import httpx
import logging
import urllib.parse
from pydantic import validate_arguments

from dracoon.client import DRACOONClient, OAuth2ConnectionType
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
            self.logger.debug("DRACOON settings adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    @validate_arguments
    async def get_settings(self, raise_on_err: bool = False) -> CustomerSettingsResponse:
        """ list customer settings (home rooms) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        try:
            res = await self.dracoon.http.get(self.api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting settings failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved customer settings.")
        return CustomerSettingsResponse(**res.json())

    @validate_arguments
    async def update_settings(self, settings_update: UpdateSettings, raise_on_err: bool = False) -> CustomerSettingsResponse:
        """ update customer settings (home rooms) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        payload = settings_update.dict(exclude_unset=True)

        try:
            res = await self.dracoon.http.put(url=self.api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating settings failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
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

    @validate_arguments
    async def get_webhooks(self, offset: int = 0, filter: str = None, limit: int = None, sort: str = None, raise_on_err: bool = False) -> WebhookList:
        """ list (all) webhooks """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        if filter: filter = urllib.parse.quote(filter)

        api_url = self.api_url + f'/webhooks/?offset={offset}'
        if filter != None: api_url += f'&filter={filter}' 
        if limit != None: api_url += f'&limit={str(limit)}' 
        if sort != None: api_url += f'&sort={sort}' 

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting webhooks failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved webhooks.")
        return WebhookList(**res.json())


    @validate_arguments
    async def create_webhook(self, hook: CreateWebhook, raise_on_err: bool = False) -> Webhook:
        """ creates a new webhook """
        payload = hook.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Creating webhook failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
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


    # get user details for given user id
    @validate_arguments
    async def get_webhook(self, hook_id: int, raise_on_err: bool = False) -> Webhook:
        """ get webhook details for specific user (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting webhook failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved webhook.")
        return Webhook(**res.json())

    @validate_arguments
    async def update_webhook(self, hook_id: int, hook_update: UpdateWebhook, raise_on_err: bool = False) -> Webhook:

        payload = hook_update.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        try:
            res = await self.dracoon.http.put(api_url, json=payload)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating webhook failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated webhook.")
        return Webhook(**res.json())


    # delete user for given user id
    @validate_arguments
    async def delete_webhook(self, hook_id: int, raise_on_err: bool = False) -> None:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/{str(hook_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Deleting webhook failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        self.logger.info("Deleted webhook.")
        return None
    
    # get user details for given user id
    @validate_arguments
    async def get_webhook_event_types(self, raise_on_err: bool = False) -> EventTypeList:

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True

        api_url = self.api_url + f'/webhooks/event_types'

        try:
            res = await self.dracoon.http.get(api_url)

            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting webhook event types failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved webhook event types.")
        return EventTypeList(**res.json())