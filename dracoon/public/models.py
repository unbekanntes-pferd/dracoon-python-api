from dataclasses import dataclass
from typing import List

@dataclass
class SystemInfo:
    languageDefault: str
    hideLoginPinputFields: bool
    s3Hosts: List[str]
    s3EnforceDirectUpload: bool
    useS3Storage: bool

@dataclass
class ActiveDirectoryInfoItem:
    id: int
    alias: str
    isGlobalAvailable: bool

@dataclass  
class ActiveDirectoryInfo:
    items: List[ActiveDirectoryInfoItem]

@dataclass
class OpenIdInfoItem:
    id: int
    issuer: str
    alias: str
    isGlobalAvailable: bool

@dataclass  
class OpenIdInfo:
    items: List[OpenIdInfoItem]

