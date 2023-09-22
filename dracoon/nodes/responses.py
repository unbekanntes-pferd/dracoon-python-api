
from enum import Enum

from pydantic import BaseModel, ConfigDict
from typing import Optional, List
from datetime import datetime

from dracoon.crypto.models import PublicKeyContainer
from dracoon.nodes.models import Permissions
from dracoon.user.models import UserInfo
from dracoon.client.models import ErrorMessage, Range

from .models import Node, NodeType


class NodeList(BaseModel):
    range: Range
    items: List[Node]


class Comment(BaseModel):
    id: int
    text: str
    createdAt: datetime
    createdBy: UserInfo
    updatedAt: datetime
    updatedBy: UserInfo
    isChanged: bool
    isDeleted: bool
    
class CommentList(BaseModel):
    range: Range
    items: List[Comment]


class DeletedNodeSummary(BaseModel):
    parentId: int
    parentPath: str
    name: str
    type: str
    cntVersions: int
    firstDeletedAt: datetime
    lastDeletedAt: datetime
    lastDeletedNodeId: int
    referenceId: Optional[int] = None
    timestampCreation: Optional[datetime] = None
    timestampModification: Optional[datetime] = None

class DeletedNodeSummaryList(BaseModel):
    range: Range
    items: List[DeletedNodeSummary]


class DeletedNode(BaseModel):
    id: Optional[int] = None
    parentId: int
    parentPath: str
    type: NodeType
    name: str
    referenceId: Optional[int] = None
    expireAt: Optional[datetime] = None
    accessedAt: Optional[datetime] = None
    isEncrypted: Optional[bool] = None
    notes: Optional[str] = None
    size: Optional[int] = None
    classification: Optional[int] = None
    createdAt: Optional[datetime] = None
    createdBy: Optional[UserInfo] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None
    deletedAt: Optional[datetime] = None
    deletedBy: Optional[UserInfo] = None

class DeletedNodeVersionsList(BaseModel):
    range: Range
    items: List[DeletedNode]

class DownloadTokenGenerateResponse(BaseModel):
    downloadUrl: str


class PresignedUrl(BaseModel):
    url: str
    partNumber: int

class PresignedUrlList(BaseModel):
    urls: List[PresignedUrl]

class CreateFileUploadResponse(BaseModel):
    uploadUrl: str
    uploadId: str
    token: str

class NodeParent(BaseModel):
    id: int
    name: str
    type: NodeType
    parentId: Optional[int] = None


class NodeParentList(BaseModel):
    items: List[NodeParent]

class Acceptance(Enum):
    accepted = "ACCEPTED"
    waiting = "WAITING"
    denied = "DENIED"


class GroupInfo(BaseModel):
    id: int
    name: str


class PendingAssignmentData(BaseModel):
    roomId: int
    roomName: str
    state: Acceptance
    userInfo: UserInfo
    groupInfo: GroupInfo

class PendingAssignmentList(BaseModel):
    range: Range
    items: List[PendingAssignmentData]

class Webhook(BaseModel):
    id: int
    name: str
    url: str
    secret: Optional[str] = None
    isEnabled: bool
    expireAt: datetime
    eventTypeNames: List[str]
    createdAt: datetime
    createdBy: Optional[UserInfo] = None
    updatedAt: datetime
    updatedBy: Optional[UserInfo] = None
    failStatus: Optional[int] = None

class RoomWebhook(BaseModel):
    isAssigned: bool
    webhook: Webhook

class RoomWebhookList(BaseModel):
    range: Range
    items: List[RoomWebhook]


class RoomUser(BaseModel):
    userInfo: UserInfo
    isGranted: bool
    permissions: Optional[Permissions] = None
    publicKeyContainer: Optional[PublicKeyContainer] = None


class RoomUserList(BaseModel):
    range: Range
    items: List[RoomUser]

class RoomGroup(BaseModel):
    id: int
    isGranted: bool
    name: str
    newGroupMemberAcceptance: Optional[str] = None
    permissions: Optional[Permissions] = None

class RoomGroupList(BaseModel):
    range: Range
    items: List[RoomGroup]
    
class S3Status(Enum):
    transfer = 'transfer' 
    finishing = 'finishing'
    done = 'done'
    error = 'error'

class S3FileUploadStatus(BaseModel):
    status: S3Status
    node: Optional[Node] = None
    errorDetails: Optional[ErrorMessage] = None
    model_config = ConfigDict(use_enum_values=True)
    
    
    
    