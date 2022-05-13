from enum import Enum
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

from dracoon.client.models import Range
from dracoon.nodes.models import Permissions
from dracoon.user.models import UserInfo


class AuditNodeInfo(BaseModel):
    nodeId: int
    nodeName: str
    nodeParentId: Optional[int]
    nodeIsEncrypted: Optional[bool]
    countChildren: Optional[int]


class AuditNodeInfoResponse(BaseModel):
    range: Range
    items: List[AuditNodeInfo]
    

class AuditUserPermission(BaseModel):
    userId: int
    userLogin: str
    userFirstName: str
    userLastName: str
    permissions: Permissions
    
class AuditNodeResponse(BaseModel):
    nodeId: int
    nodeName: str
    nodeParentPath: str
    nodeCntChildren: int
    auditUserPermissionList: List[AuditUserPermission]
    nodeParentId: Optional[int]
    nodeSize: Optional[int]
    nodeRecycleBinRetentionPeriod: Optional[int]
    nodeQuota: Optional[int]
    nodeIsEncrypted: Optional[bool]
    nodeHasActivitiesLog: Optional[bool]
    nodeCreatedAt: Optional[datetime]
    nodeCreatedBy: Optional[UserInfo]
    nodeUpdatedAt: Optional[datetime]
    nodeUpdatedBy: Optional[UserInfo]
    

class OperationStatus(Enum):
    Success = 0
    Error = 2

class LogEvent(BaseModel):
    id: int
    time: datetime
    userId: int
    message: str
    operationId: Optional[int]
    operationName: Optional[str]
    status: Optional[OperationStatus]
    userClient: Optional[str]
    customerId: Optional[int]
    userName: Optional[str]
    userIp: Optional[str]
    authParentSource: Optional[str]
    objectId1: Optional[int]
    objectName1: Optional[str]
    objectType1:Optional[str]
    objetcId2: Optional[int]
    objectName2:Optional[str]
    objectType2: Optional[str]
    attribute1: Optional[str]
    attribute2: Optional[str]
    attribute3: Optional[str]

class LogEventList(BaseModel):
    range: Range
    items: List[LogEvent]
    

