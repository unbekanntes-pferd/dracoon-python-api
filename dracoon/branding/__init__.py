
import logging
from pathlib import Path
from typing import Tuple, Optional

from dracoon.branding.models import SimpleImageRequest, UpdateBrandingRequest
from dracoon.branding.responses import CacheableBrandingResponse, ColorDetailType, ImageSize, ImageType, UpdateBrandingResponse, Upload
from dracoon.client import DRACOONClient

from dracoon.errors import ClientDisconnectedError, InvalidArgumentError, InvalidClientError

class DRACOONBranding:

    """
    API wrapper for DRACOON branding endpoint:
    Get, update branding, upload branding images
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.branding')
        
        if dracoon_client.connection:

            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.branding_base_url
    
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

        else:
            self.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')
        
    def make_updateable_branding(self, branding: UpdateBrandingResponse) -> UpdateBrandingRequest:
        """ Creates an updateable version based on existing branding """
        # get only NORMAL colors
        for color in branding.colors:
            details = [detail for detail in color.colorDetails if detail.type == ColorDetailType.NORMAL.value]
            color.colorDetails = details
            
        # remove FAVICON and INGREDIENT LOGO
        images = [SimpleImageRequest(id=image.id, type=image.type) for image in branding.images
                  if image.type != ImageType.FAV_ICON.value and image.type != ImageType.INGREDIENT_LOGO.value
                  ]

        return UpdateBrandingRequest(productName=branding.productName, colorizeHeader=branding.colorizeHeader, texts=branding.texts,
                                        colors=branding.colors, images=images, positionLoginBox=branding.positionLoginBox, 
                                        emailContact=branding.emailContact, appearanceLoginBox=branding.appearanceLoginBox, 
                                        privacyUrl=branding.privacyUrl, supportUrl=branding.supportUrl, imprintUrl=branding.imprintUrl)
    

    def make_branding_meta_update(self, branding: UpdateBrandingRequest, product_name: str = None, colorize_header: bool = None, 
                                  position_login_box: int = None, appearence_login_box: str = None, imprint_url: str = None, 
                                  support_url: str = None, privacy_url: str = None, email_contact: str = None) -> UpdateBrandingRequest:
        
        if product_name: branding.productName = product_name
        if colorize_header is not None: branding.colorizeHeader = colorize_header
        if position_login_box: branding.positionLoginBox = position_login_box
        if appearence_login_box: branding.appearanceLoginBox = appearence_login_box
        if imprint_url: branding.imprintUrl = imprint_url
        if privacy_url: branding.privacyUrl = privacy_url
        if support_url: branding.supportUrl = support_url
        if email_contact: branding.emailContact = email_contact
        
        return UpdateBrandingRequest(**branding.model_dump())
    
    def make_branding_image_update(self, branding: UpdateBrandingRequest, image_type: ImageType, image_upload: Upload):
        images = [image for image in branding.images if image.type is not image_type]
        new_image = SimpleImageRequest(id=image_upload.id, type=image_type)
        images.append(new_image)
        branding.images = images
        
        return branding
        

    async def get_branding(self, raise_on_err: bool = False) -> Optional[UpdateBrandingResponse]:
        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/v1/branding'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting branding failed.")
            return None
        
        self.logger.info("Retrieved branding.")
        return UpdateBrandingResponse(**res.json())
    
    async def update_branding(self, branding_update: UpdateBrandingRequest, raise_on_err: bool = False) -> Optional[UpdateBrandingResponse]:
        payload = branding_update.model_dump()

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/v1/branding'

        res = await self.dracoon.request('PUT', url=api_url, json=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Updating branding failed.")
            return None
        
        self.logger.info("Updated branding.")
        return UpdateBrandingResponse(**res.json())
    
    async def upload_branding_image(self, type: ImageType, file_path: str, raise_on_err: bool = False) -> Optional[Upload]:
        path = Path(file_path)
        
        if not path.exists() or not path.is_file():
            raise InvalidArgumentError("Given path is not a file.")

        if self.raise_on_err:
            raise_on_err = True
        
        with open(path, 'rb') as image: 
            payload = {
                "file": (path.name, image.read())
            }
        
        api_url = self.api_url + f'/v1/branding/files?type={type.value}'

        res = await self.dracoon.request('POST', url=api_url, files=payload, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Uploading branding image failed.")
            return None
        
        self.logger.info("Uploaded branding image.")
        return Upload(**res.json())
    
class DRACOONPublicBranding:

    """
    API wrapper for DRACOON public branding endpoint:
    Get public branding info and images
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.branding')
    
        self.dracoon = dracoon_client
        self.api_url = self.dracoon.base_url + self.dracoon.branding_base_url
    
        if self.dracoon.raise_on_err:
            self.raise_on_err = True
        else:
            self.raise_on_err = False
   
    async def get_public_branding(self, raise_on_err: bool = False) -> Optional[CacheableBrandingResponse]:

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + '/v1/public/branding'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting branding failed.")
            return None
        
        self.logger.info("Retrieved branding.")
        return CacheableBrandingResponse(**res.json())
    
    async def get_public_branding_image(self, type: ImageType, size: ImageSize, raise_on_err: bool = False) -> Optional[Tuple[bytes, str]]:

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/v1/public/branding/files/{type.value}/{size.value}'

        res = await self.dracoon.request('GET', api_url, raise_on_err=raise_on_err)

        if res is None:
            self.logger.error("Getting public branding image failed.")
            return None
        
        self.logger.info("Retrieved public branding image.")
        return res.content, res.headers["content-type"]