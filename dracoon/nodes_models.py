from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .crypto_models import FileKey

# required payload for POST /nodes/{node_id}/comments
class CommentNode(BaseModel):
    text: str

class NodeItem(BaseModel):
    id: int
    name: Optional[str]
    timestampCreation: Optional[datetime]
    timestampModification: Optional[datetime]

# required payload for POST /nodes/{node_id}/copy_to or /node/{node_id}/move_to
class TransferNode(BaseModel):
    items: List[NodeItem]
    resolutionStrategy: Optional[str]
    keepShareLinks: Optional[bool]

# required payload for POST /nodes/deleted_nodes/actions/restore
class RestoreNode(BaseModel):
    deletedNodeIds: List[int]
    resolutionStrategy: Optional[str]
    keepShareLinks: Optional[bool]
    parentId: Optional[int]

class SetFileKeysItem(BaseModel):
    fileId: int
    userId: int
    fileKey: FileKey

# required payload for POST /nodes/files/keys
class SetFileKeys(BaseModel):
    items: List[SetFileKeysItem]

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

# required payload for POST /nodes/files/uploads
class CreateUploadChannel(BaseModel):
    parentId: int
    name: str
    classification: Optional[int]
    size: Optional[int]
    expiration: Optional[Expiration]
    notes: Optional[str]
    directS3Upload: Optional[bool]
    timestampCreation: Optional[datetime]
    timestampModificiation: Optional[datetime]

# required payload for POST /nodes/folders
class CreateFolder(BaseModel):
    parentId: int
    name: str
    notes: Optional[str]
    timestampCreation: Optional[datetime]
    timestampModificiation: Optional[datetime]

# required payload for PUT /nodes/folders/{folder_id}
class UpdateFolder(BaseModel):
    name: Optional[str]
    notes: Optional[str]
    timestampCreation: Optional[datetime]
    timestampModificiation: Optional[datetime]

# required payload for POST /nodes/rooms
class CreateRoom(BaseModel):
    parentId: Optional[int]
    name: str
    notes: Optional[str]
    quota: Optional[int]
    recycleBinRetentionPeriod: Optional[int]
    inheritPermissions: Optional[bool]
    hasActivitiesLog: Optional[bool]
    newGroupMemberAcceptance: Optional[str]
    adminGroupIds: Optional[List[int]]
    adminIds: Optional[List[int]]
    classification: Optional[int]
    timestampCreation: Optional[datetime]
    timestampModificiation: Optional[datetime]

# required payload for PUT /nodes/rooms/{room_id}
class UpdateRoom(BaseModel):
    name: Optional[str]
    quota: Optional[int]
    notes: Optional[str]
    timestampCreation: Optional[datetime]
    timestampModificiation: Optional[datetime]

# required payload for PUT /nodes/rooms/{room_id}/config
class ConfigRoom(BaseModel):
    adminGroupIds: Optional[List[int]]
    adminIds: Optional[List[int]]
    recycleBinRetentionPeriod: Optional[int]
    inheritPermissions: Optional[bool]
    takeOverPermissions: Optional[bool]
    hasActivitiesLog: Optional[bool]
    newGroupMemberAcceptance: Optional[str]
    classification: Optional[int]

# required payload for PUT /nodes/files
class UpdateFiles(BaseModel):
    classification: Optional[int]
    expiration: Expiration
    objectIds: List[int]


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


class UpdateRoomUserItem(BaseModel):
    id: int
    permissions: Permissions

class UpdateRoomGroupItem(UpdateRoomUserItem):
    newGroupMemberAcceptance: Optional[str]

# required payload for PUT /nodes/rooms/{room_id}/groups
class UpdateRoomGroups(BaseModel):
    items: UpdateRoomGroupItem

# required payload for PUT /nodes/rooms/{room_id}/users
class UpdateRoomUsers(BaseModel):
    items: UpdateRoomUserItem

class UpdateRoomHookItem(BaseModel):
    webhookId: int
    isAssigned: bool

# required payload for PUT /nodes/rooms/{room_id}/webhooks
class UpdateRoomHooks(BaseModel):
    items: UpdateRoomHookItem


class ProcessRoomPendingItem(BaseModel):
    userId: int
    groupId: int
    roomId: int
    roomName: int
    state: str

# required payload for PUT /nodes/rooms/{room_id}/pending
class ProcessRoomPendingUsers(BaseModel):
    items: ProcessRoomPendingItem


























