
from pydantic import BaseModel
from typing import Optional, List

from dracoon.nodes.responses import Webhook
from dracoon.client.models import Range

class CustomerSettingsResponse(BaseModel):
    homeRoomsActive: bool
    homeRoomParentId: Optional[int]
    homeRoomParentName: Optional[str]
    homeRoomQuota: Optional[int]

class WebhookList(BaseModel):
    range: Range
    items: List[Webhook]

class EventType(BaseModel):
    id: int
    name: str
    usableTenantWebhook: bool
    usableCustomerAdminWebhook: bool
    usableNodeWebhook: bool
    usablePushNotification: bool

class EventTypeList(BaseModel):
    items: List[EventType]