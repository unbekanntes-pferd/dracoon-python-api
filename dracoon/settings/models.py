from pydantic import BaseModel
from typing import List, Optional

# required payload for PUT /settings
class UpdateSettings(BaseModel):
    homeRoomParentName: Optional[str] = None
    homeRoomQuota: Optional[int] = None
    homeRoomsActive: Optional[bool] = None

# required payload for POST /settings/webhooks
class CreateWebhook(BaseModel):
    name: str
    eventTypeNames: List[str]
    url: str
    secret: Optional[str] = None
    isEnabled: Optional[bool] = None
    triggerExampleEvent: Optional[bool] = None

# required payload for PUT /settings/webhooks/{webhook_id}
class UpdateWebhook(BaseModel):
    name: Optional[str] = None
    eventTypeNames: Optional[List[str]] = None
    url: Optional[str] = None
    secret: Optional[str] = None
    isEnabled: Optional[bool] = None
    triggerExampleEvent: Optional[bool] = None





