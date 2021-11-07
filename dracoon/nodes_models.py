from dataclasses import dataclass
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

from dracoon.user_models import UserInfo
from .crypto_models import EncryptionInfo, FileKey

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


class S3Part(BaseModel):
    partNumber: int
    partEtag: str

class CompleteS3Upload(BaseModel):
    parts: List[S3Part]
    resolutionStrategy: Optional[str]
    keepShareLinks: Optional[bool]
    fileName: Optional[str]
    fileKey: Optional[FileKey]

class GetS3Urls(BaseModel):
    firstPartNumber: int
    lastPartNumber: int
    size: int

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
    roomName: int
    state: str

# required payload for PUT /nodes/rooms/{room_id}/pending
class ProcessRoomPendingUsers(BaseModel):
    items: List[ProcessRoomPendingItem]


@dataclass
class NodeType:
    file = "file"
    folder = "folder"
    room = "room"

@dataclass
class Node:
    id: int
    type: NodeType
    name: str
    timestampCreation: Optional[datetime]
    timestampModification: Optional[datetime]
    parentId: Optional[int]
    parentPath: Optional[str]
    createdAt: Optional[datetime]
    updatedAt: Optional[datetime]
    createdBy: Optional[UserInfo]
    updatedBy: Optional[UserInfo]
    expireAt: Optional[datetime]
    hash: Optional[str]
    fileType: Optional[str]
    mediaType: Optional[str]
    size: Optional[int]
    classification: Optional[int]
    notes: Optional[str]
    permissions: Optional[Permissions]
    inheritPermissions: Optional[bool]
    isEncrypted: Optional[bool]
    encryptionInfo: Optional[EncryptionInfo]
    cntDeletedVersions: Optional[int]
    cntComments: Optional[int]
    cntDownloadShares: Optional[int]
    cntUploadShares: Optional[int]
    recycleBinRetentionPeriod: Optional[int]
    hasActivitiesLog: Optional[bool]
    quota: Optional[int]
    isFavorite: Optional[bool]
    branchVersion: Optional[int]
    mediaToken: Optional[str]
    isBrowsable: Optional[bool]
    cntRooms: Optional[int]
    contFolders: Optional[int]
    cntFiles: Optional[int]
    authParentId: Optional[int]




























