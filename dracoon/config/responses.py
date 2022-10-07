from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel

from dracoon.nodes.responses import UserInfo


class GeneralSettingsInfo(BaseModel):
    sharePasswordSmsEnabled: bool
    cryptoEnabled: bool
    emailNotificationButtonEnabled: bool
    eulaEnabled: bool
    weakPasswordEnabled: bool
    useS3Storage: bool
    s3TagsEnabled: bool
    homeRoomsActive: bool
    homeRoomParentId: Optional[int]
    subscriptionPlan: int
    
class SystemDefaults(BaseModel):
    languageDefault: Optional[str]
    downloadShareDefaultExpirationPeriod: Optional[int]
    uploadShareDefaultExpirationPeriod: Optional[int]
    fileDefaultExpirationPeriod: Optional[int]
    nonmemberViewDefault: Optional[bool]
    hideLoginInputFields: Optional[bool]
    
class InfrastructureProperties(BaseModel):
    smsConfigEnabled: Optional[bool]
    mediaServerConfiEnabled: Optional[bool]
    s3DefaultRegion: Optional[str]
    s3EnforceDirectUpload: Optional[bool]
    isDracoonCloud: Optional[bool]
    tenantUuid: Optional[str]
    
class AlgorithmStatus(Enum):
    REQUIRED = 'REQUIRED'
    DISCOURAGED = 'DISCOURAGED'
    
class AlgorithmVersionInfo(BaseModel):
    version: str
    description: str
    status: AlgorithmStatus
    
    class Config:
        use_enum_values = True
    
class AlgorithmVersionInfoList(BaseModel):
    fileKeyAlgorithms: List[AlgorithmVersionInfo]
    keyPairAlgorithms: List[AlgorithmVersionInfo]
    
class MinimumClassification(Enum):
    NO_PASSWORD = 0,
    PUBLIC = 1,
    INTERNAL = 2,
    CONFIDENTIAL = 3,
    STRICTLY_CONFIDENTIAL = 4
    
class ShareClassificationPolicies(BaseModel):
    classificationRequiresSharePassword: int
    
    class Config: 
        use_enum_values = True

class ClassificationPoliciesConfig(BaseModel):
    shareClassificationPolicies: Optional[ShareClassificationPolicies]

class PasswordExpiration(BaseModel):
    enabled: bool
    maxPasswordAge: Optional[int]

    
class CharacterRule(Enum):
    ALPHA = 'alpha'
    UPPERCASE = 'uppercase'
    LOWERCASE = 'lowercase'
    NUMERIC = 'numeric'
    SPECIAL = 'special'
    ALL = 'all'
    NONE = 'none'
    
class CharacterRules(BaseModel):
    mustContainCharacters: List[CharacterRule]
    numberOfCharacteristicsToEnforce: int
    
        
class UserLockout(BaseModel):
    enabled: bool
    maxNumberOfLoginFailures: Optional[int]
    lockoutPeriod: Optional[int]
        
class LoginPasswordPolicies(BaseModel):
    characterRules: CharacterRules
    minLength: int
    rejectDictionaryWords: bool
    rejectUserInfo: bool
    rejectKeyboardPatterns: bool
    numberOfArchivedPasswords: int
    passwordExpiration: PasswordExpiration
    userLockout: UserLockout
    updatedAt: datetime
    updatedBy: UserInfo
    
class SharesPasswordPolicies(BaseModel):
    characterRules: Optional[CharacterRules]
    minLength: Optional[int]
    rejectDictionaryWords: Optional[bool]
    rejectUserInfo: Optional[bool]
    rejectKeyboardPatterns: Optional[bool]
    updatedAt: Optional[datetime]
    updatedBy: Optional[UserInfo]
    
class EncryptionPasswordPolicies(BaseModel):
    characterRules: Optional[CharacterRules]
    minLength: Optional[int]
    rejectDictionaryWords: Optional[bool]
    rejectUserInfo: Optional[bool]
    rejectKeyboardPatterns: Optional[bool]
    updatedAt: Optional[datetime]
    updatedBy: Optional[UserInfo]  

class PasswordPoliciesConfig(BaseModel):
    loginPasswordPolicies: Optional[LoginPasswordPolicies]
    sharesPasswordPolicies: Optional[SharesPasswordPolicies]
    encryptionPasswordPolicies: Optional[EncryptionPasswordPolicies]
    
class Feature(BaseModel):
    featureId: int
    featureName: str
    isAvailable: bool
    
class FeaturedOAuthClient(BaseModel):
    isAvailable: bool
    oauthClientName: Optional[str]
    
class ProductPackagesResponse(BaseModel):
    productPackageId: int
    productPackageName: str
    features: List[Feature]
    clients: List[FeaturedOAuthClient]
    
class ProductPackageResponseList(BaseModel):
    packages: List[ProductPackagesResponse]
    
class S3Tag(BaseModel):
    id: Optional[int]
    key: Optional[str]
    value: Optional[str]
    isMandatory: Optional[bool]
    
class S3TagList(BaseModel):
    items: Optional[List[S3Tag]]