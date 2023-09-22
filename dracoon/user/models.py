from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum

from dracoon.users.models import UserAuthData
from .responses import RoleList


# required payload for PUT /user/account
class UpdateAccount(BaseModel):
    userName: Optional[str] = None
    acceptEULA: Optional[bool] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    language: Optional[str] = None

class UserGroup(BaseModel):
    id: int
    isMember: bool
    name: str

class UserAccount(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    isLocked: bool
    hasManageableRooms: bool
    userRoles: RoleList
    language: str
    authData: UserAuthData
    mudtSetEmail: Optional[bool] = None
    needsToAcceptEULA: Optional[bool] = None
    isEncryptionEnabled: Optional[bool] = None
    lastLoginSuccessAt: Optional[datetime] = None
    lastLoginFailAt: Optional[datetime] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    homeRoomId: Optional[int] = None
    userGroups: Optional[List[UserGroup]] = None

class UserType(Enum):
    internal = "internal"
    external = "external"
    system = "system"
    deleted = "deleted"

class UserInfo(BaseModel):
    id: int
    userType: UserType
    avatarUuid: Optional[str] = None
    userName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None

    
