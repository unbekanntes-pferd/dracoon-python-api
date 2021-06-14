from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from enum import Enum

### Enums 

# File key version (2048 or 4096 bit)
class FileKeyVersion(Enum):
    RSA2048_AES256GCM = 'A'
    RSA_4096_AES256GCM = 'RSA-4096/AES-256-GCM'

# Plain file key version (AES256GCM)
class PlainFileKeyVersion(Enum):
    AES256GCM = 'AES-256-GCM'

# User keypair (2048 or 4096 bit)
class UserKeyPairVersion(Enum):
    RSA2048 = 'A'
    RSA4096 = 'RSA-4096'


### Models

# file key AES256
class FileKey(BaseModel):
    key: str
    iv: str
    version: FileKeyVersion
    tag: Optional[str]

class PlainFileKey(BaseModel):
    version: PlainFileKeyVersion
    key: str
    iv: str
    tag: Optional[str]

class PublicKeyContainer(BaseModel):
    version: UserKeyPairVersion
    publicKey: str
    createdAt: Optional[datetime]
    expireAt: Optional[datetime]
    createdBy: Optional[int]

class PrivateKeyContainer(BaseModel):
    version: UserKeyPairVersion
    privateKey: str
    createdAt: Optional[datetime]
    expireAt: Optional[datetime]
    createdBy: Optional[int]

class UserKeyPairContainer(BaseModel):
    privateKeyContainer: PrivateKeyContainer
    publicKeyContainer: PublicKeyContainer

class PlainUserKeyPairContainer(BaseModel):
    privateKeyContainer: PrivateKeyContainer
    publicKeyContainer: PublicKeyContainer

