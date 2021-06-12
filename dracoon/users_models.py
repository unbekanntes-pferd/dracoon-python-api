from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

class UserAuthData(BaseModel):
    method: str
    login: Optional[str]
    password: Optional[str]
    mustChangePassword: Optional[bool]
    adConfigId: Optional[int]
    oidConfigId: Optional[str]

# required payload for POST /users
class CreateUser(BaseModel):
    firstName: str
    lastName: str
    userName: Optional[str]
    phone: Optional[str]
    expiration: Optional[Expiration]
    receiverLanguage: Optional[str]
    email: str
    notifyUser: Optional[bool]
    authData: UserAuthData
    isNonmemberViewer: Optional[bool]

# required payload for PUT /users/{user_id}
class UpdateUser(BaseModel):
    firstName: Optional[str]
    lastName: Optional[str]
    userName: Optional[str]
    isLocked: Optional[bool]
    phone: Optional[str]
    expiration: Optional[Expiration]
    receiverLanguage: Optional[str]
    email: Optional[str]
    authData: Optional[UserAuthData]
    isNonmemberViewer: Optional[bool]

class AttributeEntry(BaseModel):
    key: str
    value: str

# required payload for POST /users/{user_id}/userAttributes
class SetUserAttributes(BaseModel):
    items: List[AttributeEntry]

# required payload for PUT /users/{user_id}/userAttributes
class UpdateUserAttributes(BaseModel):
    items: Optional[List[AttributeEntry]]



