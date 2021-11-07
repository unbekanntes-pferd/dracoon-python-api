from pydantic import BaseModel
from typing import List, Optional
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from .users_models import UserAuthData

# required payload for PUT /user/account
class UpdateAccount(BaseModel):
    userName: Optional[str]
    acceptEULA: Optional[bool]
    firstName: Optional[str]
    lastName: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    language: Optional[str]

@dataclass
class Right:
    id: int
    name: str
    description: str

@dataclass
class Role:
    id: int
    name: str
    description: str
    items: Optional[List[Right]]

@dataclass
class RoleList:
    items: List[Role]


@dataclass
class UserGroup:
    id: int
    isMember: bool
    name: str


@dataclass
class UserAccount:
    id: int
    userName: str
    firstName: str
    lastName: str
    isLocked: bool
    hasManagableRooms: bool
    userRoles: RoleList
    language: str
    authData: UserAuthData
    mudtSetEmail: Optional[bool]
    needsToAcceptEULA: Optional[bool]
    isEncryptionEnabled: Optional[bool]
    lastLoginSuccessAt: Optional[datetime]
    lastLoginFailAt: Optional[datetime]
    email: Optional[str]
    phone: Optional[str]
    homeRoomId: Optional[int]
    userGroups: Optional[List[UserGroup]]

class UserType(Enum):
    internal = "internal"
    external = "external"
    system = "system"
    deleted = "deleted"


@dataclass
class UserInfo:
    id: int
    userType: UserType
    avatarUuid: str
    userName: str
    firstName: str
    lastName: str
    email: Optional[str]

    
