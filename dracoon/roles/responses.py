from typing import List
from pydantic import BaseModel

from dracoon.client.models import Range
from dracoon.nodes.responses import UserInfo

class RoleGroup(BaseModel):
    id: int
    isMember: bool
    name: str

class RoleGroupList(BaseModel):
    range: Range
    items: List[RoleGroup]
    

class RoleUser(BaseModel):
    userInfo: UserInfo
    isMember: bool
    
class RoleUserList(BaseModel):
    range: Range
    items: List[RoleUser]


    