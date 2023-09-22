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
    nodeParentId: Optional[int] = None
    nodeIsEncrypted: Optional[bool] = None
    countChildren: Optional[int] = None


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
    nodeParentId: Optional[int] = None
    nodeSize: Optional[int] = None
    nodeRecycleBinRetentionPeriod: Optional[int] = None
    nodeQuota: Optional[int] = None
    nodeIsEncrypted: Optional[bool] = None
    nodeHasActivitiesLog: Optional[bool] = None
    nodeCreatedAt: Optional[datetime] = None
    nodeCreatedBy: Optional[UserInfo] = None
    nodeUpdatedAt: Optional[datetime] = None
    nodeUpdatedBy: Optional[UserInfo] = None
    

class OperationStatus(Enum):
    Success = 0
    Error = 2

class LogEvent(BaseModel):
    id: int
    time: datetime
    userId: int
    message: str
    operationId: Optional[int] = None
    operationName: Optional[str] = None
    status: Optional[OperationStatus] = None
    userClient: Optional[str] = None
    customerId: Optional[int] = None
    userName: Optional[str] = None
    userIp: Optional[str] = None
    authParentSource: Optional[str] = None
    objectId1: Optional[int] = None
    objectName1: Optional[str] = None
    objectType1:Optional[int] = None
    objetcId2: Optional[int] = None
    objectName2:Optional[str] = None
    objectType2: Optional[int] = None
    attribute1: Optional[str] = None
    attribute2: Optional[str] = None
    attribute3: Optional[str] = None

class LogEventList(BaseModel):
    range: Range
    items: List[LogEvent]
    

