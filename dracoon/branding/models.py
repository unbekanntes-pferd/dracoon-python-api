from typing import List
from pydantic import BaseModel, ConfigDict

from dracoon.branding.responses import Color, ImageType, Text


class SimpleImageRequest(BaseModel):
    id: int
    type: ImageType
    model_config = ConfigDict(use_enum_values=True)


class UpdateBrandingRequest(BaseModel):
    productName: str
    colorizeHeader: bool
    texts: List[Text]
    colors: List[Color]
    imprintUrl: str
    privacyUrl: str
    supportUrl: str
    emailContact: str
    positionLoginBox: int
    appearanceLoginBox: str
    images: List[SimpleImageRequest]
    
    model_config = ConfigDict(use_enum_values=True)
