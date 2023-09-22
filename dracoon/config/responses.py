from datetime import datetime
from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

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
    homeRoomParentId: Optional[int] = None
    subscriptionPlan: Optional[int] = None
    
class SystemDefaults(BaseModel):
    languageDefault: Optional[str] = None
    downloadShareDefaultExpirationPeriod: Optional[int] = None
    uploadShareDefaultExpirationPeriod: Optional[int] = None
    fileDefaultExpirationPeriod: Optional[int] = None
    nonmemberViewDefault: Optional[bool] = None
    hideLoginInputFields: Optional[bool] = None
    
class InfrastructureProperties(BaseModel):
    smsConfigEnabled: Optional[bool] = None
    mediaServerConfiEnabled: Optional[bool] = None
    s3DefaultRegion: Optional[str] = None
    s3EnforceDirectUpload: Optional[bool] = None
    isDracoonCloud: Optional[bool] = None
    tenantUuid: Optional[str] = None
    
class AlgorithmStatus(Enum):
    REQUIRED = 'REQUIRED'
    DISCOURAGED = 'DISCOURAGED'
    
class AlgorithmVersionInfo(BaseModel):
    version: str
    description: str
    status: AlgorithmStatus
    model_config = ConfigDict(use_enum_values=True)
    
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


class ClassificationPoliciesConfig(BaseModel):
    shareClassificationPolicies: Optional[ShareClassificationPolicies] = None

class PasswordExpiration(BaseModel):
    enabled: bool
    maxPasswordAge: Optional[int] = None

    
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
    maxNumberOfLoginFailures: Optional[int] = None
    lockoutPeriod: Optional[int] = None
        
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
    characterRules: Optional[CharacterRules] = None
    minLength: Optional[int] = None
    rejectDictionaryWords: Optional[bool] = None
    rejectUserInfo: Optional[bool] = None
    rejectKeyboardPatterns: Optional[bool] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None
    
class EncryptionPasswordPolicies(BaseModel):
    characterRules: Optional[CharacterRules] = None
    minLength: Optional[int] = None
    rejectDictionaryWords: Optional[bool] = None
    rejectUserInfo: Optional[bool] = None
    rejectKeyboardPatterns: Optional[bool] = None
    updatedAt: Optional[datetime] = None
    updatedBy: Optional[UserInfo] = None  

class PasswordPoliciesConfig(BaseModel):
    loginPasswordPolicies: Optional[LoginPasswordPolicies] = None
    sharesPasswordPolicies: Optional[SharesPasswordPolicies] = None
    encryptionPasswordPolicies: Optional[EncryptionPasswordPolicies] = None
    
class Feature(BaseModel):
    featureId: int
    featureName: str
    isAvailable: bool
    
class FeaturedOAuthClient(BaseModel):
    isAvailable: bool
    oauthClientName: Optional[str] = None
    
class ProductPackagesResponse(BaseModel):
    productPackageId: int
    productPackageName: str
    features: List[Feature]
    clients: List[FeaturedOAuthClient]
    
class ProductPackageResponseList(BaseModel):
    packages: List[ProductPackagesResponse] = None
    
class S3Tag(BaseModel):
    id: Optional[int] = None
    key: Optional[str] = None
    value: Optional[str] = None
    isMandatory: Optional[bool] = None
    
class S3TagList(BaseModel):
    items: Optional[List[S3Tag]] = None