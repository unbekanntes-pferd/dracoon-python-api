from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime

from dracoon.crypto.models import PublicKeyContainer
from dracoon.users.models import UserAuthData
from dracoon.client.models import Range


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
    items: Optional[List[Right]] = None

class RoleList(BaseModel):
    items: List[Role]

class UserItem(BaseModel):
    id: int
    userName: str
    firstName: str
    lastName: str
    isLocked: bool
    avatarUuid: str
    createdAt: Optional[datetime] = None
    lastLoginSuccessAt: Optional[datetime] = None
    expireAt: Optional[datetime] = None
    isEncryptionEnabled: Optional[bool] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    homeRoomId: Optional[int] = None
    userRoles: Optional[RoleList] = None

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
    email: Optional[str] = None
    phone: Optional[str] = None
    expireAt: Optional[datetime] = None
    hasManageableRooms: Optional[bool] = None
    isEncryptionEnabled: Optional[bool] = None
    lastLoginSuccessAt: Optional[datetime] = None
    homeRoomId: Optional[int] = None
    publicKeyContainer: Optional[PublicKeyContainer] = None
    userRoles: Optional[RoleList] = None
    isMfaEnabled: Optional[bool] = None
    isMfaEnforced: Optional[bool] = None


class UserGroupList(BaseModel):
    range: Range
    items: List[UserGroup]


class LastAdminUserRoom(BaseModel):
    id: int
    name: str
    parentPath: str
    lastAdminInGroup: bool
    parentId: Optional[int] = None
    lastAdminInGroupId: Optional[int] = None


class LastAdminUserRoomList(BaseModel):
    items: List[LastAdminUserRoom]


class KeyValueEntry(BaseModel):
    key: str
    value: str

class AttributesResponse(BaseModel):
    range: Range
    items: List[KeyValueEntry]







