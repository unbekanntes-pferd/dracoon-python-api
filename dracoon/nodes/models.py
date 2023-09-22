
from enum import Enum
from typing_extensions import Protocol
from pydantic import BaseModel
from typing import Any, List, Optional
from datetime import datetime


from dracoon.user.models import UserInfo
from dracoon.crypto.models import EncryptionInfo, FileKey, PublicKeyContainer, UserKeyPairContainer
from dracoon.client.models import Range

# required payload for POST /nodes/{node_id}/comments
class CommentNode(BaseModel):
    text: str

class NodeItem(BaseModel):
    id: int
    name: Optional[str] = None
    timestampCreation: Optional[datetime] = None
    timestampModification: Optional[datetime] = None

# required payload for POST /nodes/{node_id}/copy_to or /node/{node_id}/move_to
class TransferNode(BaseModel):
    items: List[NodeItem]
    resolutionStrategy: Optional[str] = None
    keepShareLinks: Optional[bool] = None

# required payload for POST /nodes/deleted_nodes/actions/restore
class RestoreNode(BaseModel):
    deletedNodeIds: List[int]
    resolutionStrategy: Optional[str] = None
    keepShareLinks: Optional[bool] = None
    parentId: Optional[int] = None

class SetFileKeysItem(BaseModel):
    fileId: int
    userId: int
    fileKey: FileKey

# required payload for POST /nodes/files/keys
class SetFileKeys(BaseModel):
    items: List[SetFileKeysItem]

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: str

# required payload for POST /nodes/files/uploads
class CreateUploadChannel(BaseModel):
    parentId: int
    name: str
    classification: Optional[int] = None
    size: Optional[int] = None
    expiration: Optional[Expiration] = None
    notes: Optional[str] = None
    directS3Upload: Optional[bool] = None
    timestampCreation: Optional[str] = None
    timestampModification: Optional[str] = None


class S3Part(BaseModel):
    partNumber: int
    partEtag: str

class CompleteS3Upload(BaseModel):
    parts: List[S3Part]
    resolutionStrategy: Optional[str] = None
    keepShareLinks: Optional[bool] = None
    fileName: Optional[str] = None
    fileKey: Optional[FileKey] = None


class CompleteUpload(BaseModel):
    resolutionStrategy: Optional[str] = None
    keepShareLinks: Optional[bool] = None
    fileName: Optional[str] = None
    fileKey: Optional[FileKey] = None
    
class GetS3Urls(BaseModel):
    firstPartNumber: int
    lastPartNumber: int
    size: int

# required payload for POST /nodes/folders
class CreateFolder(BaseModel):
    parentId: int
    name: str
    notes: Optional[str] = None
    timestampCreation: Optional[datetime] = None
    timestampModificiation: Optional[datetime] = None

# required payload for PUT /nodes/folders/{folder_id}
class UpdateFolder(BaseModel):
    name: Optional[str] = None
    notes: Optional[str] = None
    timestampCreation: Optional[str] = None
    timestampModificiation: Optional[str] = None

# required payload for POST /nodes/rooms
class CreateRoom(BaseModel):
    parentId: Optional[int] = None
    name: str
    notes: Optional[str] = None
    quota: Optional[int] = None
    recycleBinRetentionPeriod: Optional[int] = None
    inheritPermissions: Optional[bool] = None
    hasActivitiesLog: Optional[bool] = None
    newGroupMemberAcceptance: Optional[str] = None
    adminGroupIds: Optional[List[int]] = None
    adminIds: Optional[List[int]] = None
    classification: Optional[int] = None
    timestampCreation: Optional[str] = None
    timestampModificiation: Optional[str] = None

# required payload for PUT /nodes/rooms/{room_id}
class UpdateRoom(BaseModel):
    name: Optional[str] = None
    quota: Optional[int] = None
    notes: Optional[str] = None
    timestampCreation: Optional[str] = None
    timestampModificiation: Optional[str] = None

# required payload for PUT /nodes/rooms/{room_id}/config
class ConfigRoom(BaseModel):
    adminGroupIds: Optional[List[int]] = None
    adminIds: Optional[List[int]] = None
    recycleBinRetentionPeriod: Optional[int] = None
    inheritPermissions: Optional[bool] = None
    takeOverPermissions: Optional[bool] = None
    hasActivitiesLog: Optional[bool] = None
    newGroupMemberAcceptance: Optional[str] = None
    classification: Optional[int] = None

# required payload for PUT /nodes/files
class UpdateFiles(BaseModel):
    classification: Optional[int] = None
    expiration: Optional[Expiration] = None
    objectIds: List[int]

class UpdateFile(BaseModel):
    name: Optional[str] = None
    expiration: Optional[Expiration] = None
    classification: Optional[int] = None
    notes: Optional[str] = None
    timestampCreation: Optional[str] = None
    timestampModification: Optional[str] = None


class Permissions(BaseModel):
    manage: bool
    read: bool
    create: bool
    change: bool
    delete: bool
    manageDownloadShare: bool
    manageUploadShare: bool
    readRecycleBin: bool
    restoreRecycleBin: bool
    deleteRecycleBin: bool
    
class EncryptRoom(BaseModel):
    isEncrypted: bool
    useDataSpaceRescueKey: Optional[bool] = None
    dataRoomRescueKey: Optional[UserKeyPairContainer] = None


class UpdateRoomUserItem(BaseModel):
    id: int
    permissions: Permissions

class UpdateRoomGroupItem(UpdateRoomUserItem):
    id: int
    permissions: Permissions
    newGroupMemberAcceptance: Optional[str] = None

# required payload for PUT /nodes/rooms/{room_id}/groups
class UpdateRoomGroups(BaseModel):
    items: List[UpdateRoomGroupItem]

# required payload for PUT /nodes/rooms/{room_id}/users
class UpdateRoomUsers(BaseModel):
    items: List[UpdateRoomUserItem]

class UpdateRoomHookItem(BaseModel):
    webhookId: int
    isAssigned: bool

# required payload for PUT /nodes/rooms/{room_id}/webhooks
class UpdateRoomHooks(BaseModel):
    items: List[UpdateRoomHookItem]


class ProcessRoomPendingItem(BaseModel):
    userId: int
    groupId: int
    roomId: int
    roomName: str
    state: str

# required payload for PUT /nodes/rooms/{room_id}/pending
class ProcessRoomPendingUsers(BaseModel):
    items: List[ProcessRoomPendingItem]


class NodeType(Enum):
    file = "file"
    folder = "folder"
    room = "room"

class Node(BaseModel):
    id: int
    type: NodeType
    referenceId: Optional[int] = None
    name: str
    timestampCreation: Optional[datetime] = None
    timestampModification: Optional[datetime] = None
    parentId: Optional[int] = None
    parentPath: Optional[str] = None
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None
    createdBy: Optional[UserInfo] = None
    updatedBy: Optional[UserInfo] = None
    expireAt: Optional[datetime] = None
    hash: Optional[str] = None
    fileType: Optional[str] = None
    mediaType: Optional[str] = None
    size: Optional[int] = None
    classification: Optional[int] = None
    notes: Optional[str] = None
    permissions: Optional[Permissions] = None
    inheritPermissions: Optional[bool] = None
    isEncrypted: Optional[bool] = None
    encryptionInfo: Optional[EncryptionInfo] = None
    cntDeletedVersions: Optional[int] = None
    cntComments: Optional[int] = None
    cntDownloadShares: Optional[int] = None
    cntUploadShares: Optional[int] = None
    recycleBinRetentionPeriod: Optional[int] = None
    hasActivitiesLog: Optional[bool] = None
    quota: Optional[int] = None
    isFavorite: Optional[bool] = None
    branchVersion: Optional[int] = None
    mediaToken: Optional[str] = None
    isBrowsable: Optional[bool] = None
    cntRooms: Optional[int] = None
    cntFolders: Optional[int] = None
    cntFiles: Optional[int] = None
    authParentId: Optional[int] = None
    
class LogEvent(BaseModel):
    id: int
    time: datetime
    userId: int
    message: str
    operationId: Optional[int] = None
    operationName: Optional[str] = None
    status: Optional[int] = None
    userClient: Optional[str] = None
    customerId: Optional[int] = None
    userName: Optional[str] = None
    userIp: Optional[str] = None
    authParentSource: Optional[str] = None
    authParentTarget: Optional[str] = None
    objectId1: Optional[int] = None
    objectType1: Optional[int] = None
    objectName1: Optional[str] = None
    objectId2: Optional[int] = None
    objectType2: Optional[int] = None
    objectName2: Optional[str] = None
    attribute1: Optional[str] = None
    attribute2: Optional[str] = None
    attribute3: Optional[str] = None
    
class LogEventList(BaseModel):
    range: Range
    items: List[LogEvent]
    
class FileFileKeys(BaseModel):
    id: int
    fileKeyContainer: FileKey
    
class UserUserPublicKey(BaseModel):
    id: int
    publicKeyContainer: PublicKeyContainer
    
class UserIdFileIdItem(BaseModel):
    userId: int 
    fileId: int
    
class MissingKeysResponse(BaseModel):
    range: Range
    items: List[UserIdFileIdItem]
    users: List[UserUserPublicKey]
    files: List[FileFileKeys]
    
class FileVersion(BaseModel):
    id: int
    referenceId: int
    name: str
    parentId: Optional[int] = None
    deleted: Optional[bool] = None
    
class FileVersionList(BaseModel):
    range: Range
    items: List[FileVersion]
    

class Callback(Protocol):
    """ callback function signature - example see TransferJob.update_progress() """
    def __call__(self, val: int, total: int = ...) -> Any:
        ...
        
class TransferJob:
    """ object representing a single transfer (up- / download) """
    progress = 0
    transferred = 0
    total = 0
    
    def update_progress(self, val: int, total: int = None) -> None:
        self.transferred += val
        if total is not None and self.total == 0:
            # only set total if present and not set
            self.total = total
        
    @property
    def progress(self):
        if self.total > 0:
            return self.transferred / self.total
        else:
            return 0





























