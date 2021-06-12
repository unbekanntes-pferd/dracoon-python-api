from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .crypto_models import UserKeyPairContainer

# required payload for PUT /settings
class UpdateSettings(BaseModel):
    homeRoomParentName: Optional[str]
    homeRoomQuota: Optional[int]
    homeRoomsActive: Optional[bool]

# required payload for POST /settings/webhooks
class CreateWebhook(BaseModel):
    name: str
    eventTypeNames: List[str]
    url: str
    secret: Optional[str]
    isEnabled: Optional[bool]
    triggerExampleEvent: Optional[bool]

# required payload for PUT /settings/webhooks/{webhook_id}
class UpdateWebhook(BaseModel):
    name: Optional[str]
    eventTypeNames: Optional[List[str]]
    url: Optional[str]
    secret: Optional[str]
    isEnabled: Optional[bool]
    triggerExampleEvent: Optional[bool]





