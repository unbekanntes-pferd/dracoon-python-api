from pydantic import BaseModel
from typing import Optional

# required payload for PUT /user/account
class UpdateAccount(BaseModel):
    userName: Optional[str]
    acceptEULA: Optional[bool]
    firstName: Optional[str]
    lastName: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    language: Optional[str]
    
