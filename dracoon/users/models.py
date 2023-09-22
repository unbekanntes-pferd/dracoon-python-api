from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

class UserAuthData(BaseModel):
    method: str
    login: Optional[str] = None
    password: Optional[str] = None
    mustChangePassword: Optional[bool] = None
    adConfigId: Optional[int] = None
    oidConfigId: Optional[int] = None

class UserAuthMethodOption(BaseModel):
    key: str
    value: str

class UserAuthMethod(BaseModel):
    authId: str
    isEnabled: bool
    options: Optional[List[UserAuthMethodOption]] = None

class MfaConfig(BaseModel):
    mfaEnforced: Optional[bool] = None

# required payload for POST /users
class CreateUser(BaseModel):
    firstName: str
    lastName: str
    userName: Optional[str] = None
    phone: Optional[str] = None
    expiration: Optional[Expiration] = None
    receiverLanguage: Optional[str] = None
    email: str
    notifyUser: Optional[bool] = None
    authData: UserAuthData
    isNonmemberViewer: Optional[bool] = None
    mfaConfig: Optional[MfaConfig] = None

# required payload for PUT /users/{user_id}
class UpdateUser(BaseModel):
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    userName: Optional[str] = None
    isLocked: Optional[bool] = None
    phone: Optional[str] = None
    expiration: Optional[Expiration] = None
    receiverLanguage: Optional[str] = None
    email: Optional[str] = None
    authData: Optional[UserAuthData] = None
    authMethods: Optional[List[UserAuthMethod]] = None
    isNonmemberViewer: Optional[bool] = None
    mfaConfig: Optional[MfaConfig] = None

class AttributeEntry(BaseModel):
    key: str
    value: str
    
# required payload for POST /users/{user_id}/userAttributes (deprecated)
class SetUserAttributes(BaseModel):
    items: List[AttributeEntry]

# required payload for PUT /users/{user_id}/userAttributes
class UpdateUserAttributes(BaseModel):
    items: Optional[List[AttributeEntry]] = None






