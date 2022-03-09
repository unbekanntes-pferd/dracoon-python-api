from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

from dracoon.nodes.models import NodeType, UserInfo
from dracoon.client.models import Range

class DownloadShare(BaseModel):
    id: int
    name: str
    nodeId: int
    accessKey: str
    cntDownloads: int
    createdAt: datetime
    createdBy: UserInfo
    updatedAt: Optional[datetime]
    updatedBy: Optional[UserInfo]
    notes: Optional[str]
    internalNotes: Optional[str]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    isProtected: Optional[bool]
    expireAt: Optional[datetime]
    maxDownloads: Optional[int]
    nodePath: Optional[str]
    dataUrl: Optional[str]
    isEncrypted: Optional[bool]
    nodeType: Optional[NodeType]

class DownloadShareList(BaseModel):
    range: Range
    items: List[DownloadShare]

class UploadShare(BaseModel):
    id: int
    name: str
    targetId: int
    isProtected: bool
    accessKey: str
    createdAt: datetime
    createdBy: UserInfo
    updatedAt: Optional[datetime]
    updatedBy: Optional[UserInfo]
    expireAt: Optional[datetime]
    targetPath: Optional[str]
    isEncrypted: Optional[bool]
    notes: Optional[str]
    internalNotes: Optional[str]
    filesExpiryPeriod: Optional[int]
    cntFiles: Optional[int]
    cntUploads: Optional[int]
    showUploadedFiles: Optional[bool]
    dataUrl: Optional[str]
    maxSlots: Optional[int]
    maxSite: Optional[int]
    targetType: Optional[NodeType]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]

class UploadShareList(BaseModel):
    range: Range
    items: List[UploadShare]

