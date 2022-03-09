from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from dracoon.crypto.models import UserKeyPairContainer, FileKey

class Expiration(BaseModel):
    enableExpiration: bool
    expireAt: datetime

# required payload for POST /shares/downloads
class CreateShare(BaseModel):
    nodeId: int
    name: Optional[str]
    password: Optional[str]
    expiration: Optional[Expiration]
    notes: Optional[str]
    internalNotes: Optional[str]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    maxDownloads: Optional[int]
    keyPair: Optional[UserKeyPairContainer]
    fileKey: Optional[FileKey]
    reciverLanguage: Optional[str]
    textMessageRecipients: Optional[List[str]]

# required payload for PUT /shares/downloads
class UpdateShares(BaseModel):
    expiration: Optional[Expiration]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    maxDownloads: Optional[int]
    resetMaxDownloads: Optional[bool]
    objectIds: List[int]

# required payload for PUT /shares/downloads/{share_id}
class UpdateShare(BaseModel):
    expiration: Optional[Expiration]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    maxDownloads: Optional[int]
    resetMaxDownloads: Optional[bool]
    name: Optional[str]
    password: Optional[str]
    notes: Optional[str]
    internalNotes: Optional[str]
    defaultCountry: Optional[str]
    resetPassword: Optional[bool]

# required payload for POST /shares/downloads/{share_id}/email and /shares/loads/{share_id}/email 
class SendShare(BaseModel):
    recipients: List[str]
    body: str
    receiverLanguage: Optional[str]

# required payload for POST /shares/uploads
class CreateFileRequest(BaseModel):
    targetId: int
    name: Optional[str]
    password: Optional[str]
    expiration: Optional[Expiration]
    filesExpiryPeriod: Optional[int]
    notes: Optional[str]
    internalNotes: Optional[str]
    showUploadedFiles: Optional[bool]
    maxSlots: Optional[int]
    maxSize: Optional[int]
    receiverLanguage: Optional[str]
    textMessageRecipients: Optional[List[str]]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]

# required payload for PUT /shares/uploads
class UpdateFileRequests(BaseModel):
    expiration: Optional[Expiration]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    showUploadedFiles: Optional[bool]
    maxSlots: Optional[int]
    maxSize: Optional[int]
    filesExpiryPeriod: Optional[int]
    resetFilesExpiryPeriod: Optional[bool]
    objectIds: List[int]

# required payload for PUT /shares/uploads/{share_id}
class UpdateFileRequest(BaseModel):
    name: Optional[str]
    password: Optional[str]
    expiration: Optional[Expiration]
    notes: Optional[str]
    internalNotes: Optional[str]
    showCreatorName: Optional[bool]
    showCreatorUsername: Optional[bool]
    showUploadedFiles: Optional[bool]
    maxSlots: Optional[int]
    maxSize: Optional[int]
    filesExpiryPeriod: Optional[int]
    resetFilesExpiryPeriod: Optional[bool]
    resetMaxSize: Optional[bool]
    resetMaxSlots: Optional[bool]
    textMessageRecipients: Optional[List[str]]
    defaultCountry: Optional[str]
    resetPassword: Optional[bool]
    receiverLanguage: Optional[str]




    






