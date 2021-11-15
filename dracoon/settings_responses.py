from .core_models import Range
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from .nodes_responses import Webhook

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