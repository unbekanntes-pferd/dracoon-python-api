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
    name: Optional[str] = None
    password: Optional[str] = None
    expiration: Optional[Expiration] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    maxDownloads: Optional[int] = None
    keyPair: Optional[UserKeyPairContainer] = None
    fileKey: Optional[FileKey] = None
    receiverLanguage: Optional[str] = None
    textMessageRecipients: Optional[List[str]] = None

# required payload for PUT /shares/downloads
class UpdateShares(BaseModel):
    expiration: Optional[Expiration] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    maxDownloads: Optional[int] = None
    resetMaxDownloads: Optional[bool] = None
    objectIds: List[int]

# required payload for PUT /shares/downloads/{share_id}
class UpdateShare(BaseModel):
    expiration: Optional[Expiration] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    maxDownloads: Optional[int] = None
    resetMaxDownloads: Optional[bool] = None
    name: Optional[str] = None
    password: Optional[str] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    defaultCountry: Optional[str] = None
    resetPassword: Optional[bool] = None
    receiverLanguage: Optional[str] = None

# required payload for POST /shares/downloads/{share_id}/email and /shares/loads/{share_id}/email 
class SendShare(BaseModel):
    recipients: List[str]
    body: str
    receiverLanguage: Optional[str] = None

# required payload for POST /shares/uploads
class CreateFileRequest(BaseModel):
    targetId: int
    name: Optional[str] = None
    password: Optional[str] = None
    expiration: Optional[Expiration] = None
    filesExpiryPeriod: Optional[int] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    showUploadedFiles: Optional[bool] = None
    maxSlots: Optional[int] = None
    maxSize: Optional[int] = None
    receiverLanguage: Optional[str] = None
    textMessageRecipients: Optional[List[str]] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None

# required payload for PUT /shares/uploads
class UpdateFileRequests(BaseModel):
    expiration: Optional[Expiration]
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    showUploadedFiles: Optional[bool] = None
    maxSlots: Optional[int] = None
    maxSize: Optional[int] = None
    filesExpiryPeriod: Optional[int] = None
    resetFilesExpiryPeriod: Optional[bool] = None
    objectIds: List[int]

# required payload for PUT /shares/uploads/{share_id}
class UpdateFileRequest(BaseModel):
    name: Optional[str] = None
    password: Optional[str] = None
    expiration: Optional[Expiration] = None
    notes: Optional[str] = None
    internalNotes: Optional[str] = None
    showCreatorName: Optional[bool] = None
    showCreatorUsername: Optional[bool] = None
    showUploadedFiles: Optional[bool] = None
    maxSlots: Optional[int] = None
    maxSize: Optional[int] = None
    filesExpiryPeriod: Optional[int] = None
    resetFilesExpiryPeriod: Optional[bool] = None
    resetMaxSize: Optional[bool] = None
    resetMaxSlots: Optional[bool] = None
    textMessageRecipients: Optional[List[str]] = None
    defaultCountry: Optional[str] = None
    resetPassword: Optional[bool] = None
    receiverLanguage: Optional[str] = None




    






