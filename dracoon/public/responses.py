from pydantic import BaseModel
from typing import List, Optional


class SystemInfo(BaseModel):
    languageDefault: str
    hideLoginInputFields: bool
    s3Hosts: List[str]
    s3EnforceDirectUpload: bool
    useS3Storage: bool


class AuthADInfo(BaseModel):
    id: int
    alias: str
    isGlobalAvailable: bool


class AuthADInfoList(BaseModel):
    items: List[AuthADInfo]


class AuthOIDCInfo(BaseModel):
    id: int
    name: str
    issuer: str
    mappingClaim: str
    isGlobalAvailable: bool
    userManagementUrl: Optional[str]


class AuthOIDCInfoList(BaseModel):
    items: List[AuthOIDCInfo]
