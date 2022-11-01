
import logging
from pathlib import Path
from typing import Tuple

import httpx
from dracoon.branding.models import SimpleImageRequest, UpdateBrandingRequest
from dracoon.branding.responses import CacheableBrandingResponse, ColorDetailType, ImageSize, ImageType, UpdateBrandingResponse, Upload
from dracoon.client import DRACOONClient, OAuth2ConnectionType

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

            self.logger.debug("DRACOON config adapter created.")
        
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
        
        return UpdateBrandingRequest(**branding.dict())
    
    def make_branding_image_update(self, branding: UpdateBrandingRequest, image_type: ImageType, image_upload: Upload):
        images = [image for image in branding.images if image.type is not image_type]
        new_image = SimpleImageRequest(id=image_upload.id, type=image_type)
        images.append(new_image)
        branding.images = images
        
        return branding
        

    async def get_branding(self, raise_on_err: bool = False) -> UpdateBrandingResponse:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/v1/branding'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting branding failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved branding.")
        return UpdateBrandingResponse(**res.json())
    
    async def update_branding(self, branding_update: UpdateBrandingRequest, raise_on_err: bool = False) -> UpdateBrandingResponse:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
            
        payload = branding_update.dict()

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/v1/branding'

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Updating branding failed.")
            print(e.response.json())
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Updated branding.")
        return UpdateBrandingResponse(**res.json())
    
    async def upload_branding_image(self, type: ImageType, file_path: str, raise_on_err: bool = False) -> Upload:
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)
            
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

        try:
            res = await self.dracoon.http.post(url=api_url, files=payload)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            print(e.response.json())
            self.logger.error("Uploading branding image failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
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

            self.logger.debug("DRACOON public branding adapter created.")
            
    async def get_public_branding(self) -> CacheableBrandingResponse:

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/v1/public/branding'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting branding failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved branding.")
        return CacheableBrandingResponse(**res.json())
    
    async def get_public_branding_image(self, type: ImageType, size: ImageSize) -> Tuple[bytes, str]:

        if self.raise_on_err:
            raise_on_err = True
        
        api_url = self.api_url + f'/v1/public/branding/files/{type.value}/{size.value}'

        try:
            res = await self.dracoon.http.get(api_url)
            res.raise_for_status()
            content_type = res.headers["content-type"]
            image = res.content
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Getting public branding image failed.")
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        
        self.logger.info("Retrieved public branding image.")
        return image, content_type