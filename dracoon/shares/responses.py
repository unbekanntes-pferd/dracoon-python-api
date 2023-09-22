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
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    isProtected: Optional[bool] = None
    expireAt: Optional[datetime] = None
    maxDownloads: Optional[int] = None
    nodePath: Optional[str] = None
    dataUrl: Optional[str] = None
    isEncrypted: Optional[bool] = None
    nodeType: Optional[NodeType] = None

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
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None
    expireAt: Optional[datetime] = None
    targetPath: Optional[str] = None
    isEncrypted: Optional[bool] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    filesExpiryPeriod: Optional[int] = None
    cntFiles: Optional[int] = None
    cntUploads: Optional[int] = None
    showUploadedFiles: Optional[bool] = None
    dataUrl: Optional[str] = None
    maxSlots: Optional[int] = None
    maxSite: Optional[int] = None
    targetType: Optional[NodeType] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None

class UploadShareList(BaseModel):
    range: Range
    items: List[UploadShare]

