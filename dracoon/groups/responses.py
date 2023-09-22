from typing import List, Optional
from pydantic import BaseModel
from datetime import datetime
from enum import Enum

from dracoon.user.responses import RoleList
from dracoon.client.models import Range

class UserType(Enum):
    internal = "internal"
    external = "external"
    system = "system"
    deleted = "deleted"
    

class UserInfo(BaseModel):
    id: int
    userType: UserType
    avatarUuid: str
    userName: Optional[str] = None
    firstName: Optional[str] = None
    lastName: Optional[str] = None
    email: Optional[str] = None


class Group(BaseModel):
    id: int
    name: str
    createdAt: datetime
    createdBy: UserInfo
    cntUsers: int
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None
    expireAt: Optional[datetime] = None
    groupRoles:Optional[RoleList] = None

class GroupList(BaseModel):
    range: Range
    items: List[Group]

class GroupUser(BaseModel):
    userInfo: UserInfo
    isMember: bool

class GroupUserList(BaseModel):
    range: Range
    items: List[GroupUser]

class LastAdminGroupRoom(BaseModel):
    id: int
    name: str
    parentPath: str
    parentId: Optional[int] = None

class LastAdminGroupRoomList(BaseModel):
    items: List[LastAdminGroupRoom]


