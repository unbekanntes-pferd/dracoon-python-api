
from .crypto_models import PublicKeyContainer
from .users_models import UserAuthData
from .core_models import Range
from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

class UserGroup(BaseModel):
    id: int
    isMember: bool
    name: str

class Right(BaseModel):
    id: int
    name: str
    description: str

class Role(BaseModel):
    id: int
    name: str
    description: str
    items: Optional[List[Right]]

class RoleList(BaseModel):
    items: List[Role]

class UserItem(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    isLocked: bool
    avatarUuid: str
    createdAt: Optional[datetime]
    lastLoginSuccessAt: Optional[datetime]
    expireAt: Optional[datetime]
    isEncryptionEnabled: Optional[bool]
    email: Optional[str]
    phone: Optional[str]
    homeRoomId: Optional[int]
    userRoles: Optional[RoleList]

class UserList(BaseModel):
    range: Range
    items: List[UserItem]


class UserData(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    isLocked: bool
    avatarUuid: str
    authData: UserAuthData
    email: Optional[str]
    phone: Optional[str]
    expireAt: Optional[datetime]
    hasManageableRooms: Optional[bool]
    isEncryptionEnabled: Optional[bool]
    lastLoginSuccessAt: Optional[datetime]
    homeRoomId: Optional[int]
    publicKeyContainer: Optional[PublicKeyContainer]
    userRoles: Optional[RoleList]


class UserGroupList(BaseModel):
    range: Range
    items: List[UserGroup]


class LastAdminUserRoom(BaseModel):
    id: int
    name: str
    parentPath: str
    lastAdminInGroup: bool
    parentId: Optional[int]
    lastAdminInGroupId: Optional[int]


class LastAdminUserRoomList(BaseModel):
    items: List[LastAdminUserRoom]


class KeyValueEntry(BaseModel):
    key: str
    value: str

class AttributesResponse(BaseModel):
    range: Range
    items: List[KeyValueEntry]







