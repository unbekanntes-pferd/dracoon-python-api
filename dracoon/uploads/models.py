from pydantic import BaseModel
from typing import Optional, List
from dracoon.crypto.models import FileKey

class UploadChannelResponse(BaseModel):
    uploadUrl: str
    uploadId: str
    token: str

class UserFileKey(BaseModel):
    userId: int
    fileKey: FileKey

class UserFileKeyList(BaseModel):
    items: List[UserFileKey]

class FinalizeUpload(BaseModel):
    resolutionStrategy: Optional[str] = None
    keepShareLinks: Optional[bool] = None
    fileName: Optional[str] = None
    fileKey: Optional[FileKey] = None
    userFileKeyList: Optional[UserFileKeyList] = None

    
