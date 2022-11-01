from typing import List
from enum import Enum
from pydantic import BaseModel

class ColorDetailType(Enum):
    NORMAL = 'normal'
    LIGHT = 'light'
    DARK = 'dark'
    TEXT = 'text'
    
class TextType(Enum):
    EMAIL_SIGNATURE = 'emailSignature'
    TERMS = 'terms'

class ImageType(Enum):
    WEB_LOGO = 'webLogo'
    APP_LOGO = 'appLogo'
    SQUARED_LOGO = 'squaredLogo'
    APP_SPLASH_IMAGE = 'appSplashImage'
    WEB_SPLASH_IMAGE = 'webSplashImage'
    FAV_ICON = 'favIcon'
    INGREDIENT_LOGO = 'ingredientLogo'

class ImageSize(Enum):
    SMALL = 'small'
    MEDIUM = 'medium'
    LARGE = 'large'

class Language(BaseModel):
    languageTag: str
    content: str

class Text(BaseModel):
    type: TextType
    languages: List[Language]
    class Config:
        use_enum_values = True

class ColorDetails(BaseModel):
    type: ColorDetailType
    rgba: str
    class Config:
        use_enum_values = True

class Color(BaseModel):
    type: str
    colorDetails: List[ColorDetails]

class SimpleImageResponse(BaseModel):
    id: int
    url: str
    type: ImageType
    class Config:
        use_enum_values = True

class UpdateBrandingResponse(BaseModel):
    productName: str
    colors: List[Color]
    colorizeHeader: bool
    texts: List[Text]
    imprintUrl: str
    privacyUrl: str
    supportUrl: str
    emailContact: str
    images: List[SimpleImageResponse]
    positionLoginBox: int
    appearanceLoginBox: str
    
class Upload(BaseModel):
    id: int
    createdAt: str
    
class CacheableBrandingFileResponse(BaseModel):
    size: ImageSize
    url: str
    
class CacheableBrandingImageResponse(BaseModel):
    type: ImageType
    files: List[CacheableBrandingFileResponse]
  
class CacheableBrandingResponse(BaseModel):
    createdAt: str
    changedAt: str
    productName: str
    colors: List[Color]
    colorizeHeader: bool
    imprintUrl: str
    privacyUrl: str
    supportUrl: str
    emailContact: str
    images: List[CacheableBrandingImageResponse]
    positionLoginBox: int
    appearanceLoginBox: str
    texts: List[Text]

    