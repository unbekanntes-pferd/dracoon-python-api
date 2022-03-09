from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

# required payload for POST /groups
class CreateGroup(BaseModel):
    name: str
    expiration: Optional[Expiration]

# required payload for PUT /groups/{group_id}
class UpdateGroup(BaseModel):
    name: Optional[str]
    expiration: Optional[Expiration]