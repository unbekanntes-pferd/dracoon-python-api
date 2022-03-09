"""
Async DRACOON downloads adapter based on httpx, tqdm and pydantic
V1.1.0
(c) Octavio Simone, February 2022 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/downloads
Please note: maximum 500 items are returned in GET requests
 - refer to documentation on how to upload files:
https://support.dracoon.com/hc/de/articles/115005512089

"""
from pathlib import Path
import logging

from tqdm import tqdm
import httpx

from dracoon.nodes import CHUNK_SIZE
from dracoon.nodes.models import Node, NodeType
from dracoon.crypto.models import FileKey, PlainUserKeyPairContainer
from dracoon.client import DRACOONClient
from dracoon.crypto import FileDecryptionCipher, decrypt_file_key


class DRACOONDownloads:

    """
    API wrapper for DRACOON uploads endpoint:
    Upload files via proxy upload with given open upload channel.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/user'
            self.logger = logging.getLogger('dracoon.downloads')
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

            self.logger.debug("DRACOON downloads adapter created.")
   
        else:
            self.dracoon.logger.critical("DRACOON client not connected.")
            raise ValueError(
                'DRACOON client must be connected: client.connect()')

    
    def check_file_exists(self, path: str) -> bool:
        """ Check if a file already exists. """

        file = Path(path)

        return file.exists() and file.is_file()

    
    async def download_unencrypted(self, download_url: str, target_path: str, node_info: Node, chunksize: int = CHUNK_SIZE, raise_on_err: bool = False,
                                   display_progress: bool = False):
        """ Download a file from an unecrypted data room. """

        self.logger.info("Download started.")
        self.logger.debug("Download to %s", target_path)

        if self.raise_on_err:
            raise_on_err = True
        
        if node_info.type != NodeType.file:
            self.logger.critical("Invalid node type: %s", node_info.type)
            raise TypeError('Ony file download possible.')

        file_path = target_path + '/' + node_info.name

        if self.check_file_exists(file_path):
            self.logger.critical("File already exists: %s", file_path)
            raise ValueError('File already exists.')

        folder = Path(target_path)

        if not folder.is_dir():
            self.logger.critical("Target path is not a folder.")
            raise ValueError(f'A folder needs to be provided. {target_path} is not a folder.')
        
        size = node_info.size

        self.logger.debug("File download for size: %s", size)
        self.logger.debug("Using chunksize: %s", chunksize)
            
        try:
            async with httpx.AsyncClient() as downloader:
                
                file_out = open(file_path, 'wb')
                
                async with downloader.stream(method='GET', url=download_url) as res:
                    
                    if display_progress: progress = tqdm(unit='iMB',unit_divisor=1024, total=size, unit_scale=True, desc=node_info.name)
                    async for chunk in res.aiter_bytes(chunksize):
                        file_out.write(chunk)
                        if display_progress: progress.update(len(chunk))
                                        
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        finally:
            if file_out: file_out.close()
            if display_progress and progress: progress.close()
                   
        self.logger.info("Download completed.")
            

    async def download_encrypted(self, download_url: str, target_path: str, node_info: Node, plain_keypair: PlainUserKeyPairContainer, file_key: FileKey, 
                                       chunksize: int = CHUNK_SIZE, raise_on_err: bool = False, display_progress: bool = False):   
        """ Download a file from an encrypted data room. """

        self.logger.info("Download started.")
        self.logger.debug("Download to %s", target_path)

        if self.raise_on_err:
            raise_on_err = True
            
        if not node_info:
            raise ValueError('File does not exist.')
        
        if node_info.type != NodeType.file:
            raise TypeError('Ony file download possible.')

        file_path = target_path + '/' + node_info.name

        if self.check_file_exists(file_path):
            await self.dracoon.logout()
            self.logger.critical("File already exists: %s", file_path)
            raise ValueError('File already exists.')

        folder = Path(target_path)

        if not folder.is_dir():
            await self.dracoon.logout()
            self.logger.critical("Target path is not a folder.")
            raise ValueError(f'A file needs to be provided. {target_path} is not a folder.')
        
        size = node_info.size

        plain_file_key = decrypt_file_key(file_key=file_key, keypair=plain_keypair)
        decryptor = FileDecryptionCipher(plain_file_key=plain_file_key)

        self.logger.debug("File download for size: %s", size)
        self.logger.debug("Using chunksize: %s", chunksize)

        try:    
            async with httpx.AsyncClient() as downloader:
                
                file_out = open(file_path, 'wb')  
                
                async with downloader.stream(method='GET', url=download_url) as res:
                    res.raise_for_status()
                    if display_progress: progress = tqdm(unit='iMB',unit_divisor=1024, total=size, unit_scale=True, desc=node_info.name)   
                    
                    # decrypt file and then write to disk
                    async for chunk in res.aiter_bytes(chunksize):            
                        plain_chunk = decryptor.decode_bytes(chunk)
                        file_out.write(plain_chunk)
                        if display_progress: progress.update(len(chunk))
                        
                        # finalize encryption after last chunk
                        if not chunk:
                            last_data = decryptor.finalize()
                            file_out.write(last_data)
                                     
                    self.logger.info("Download completed.")
        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
        finally:
            if file_out: file_out.close()
            if display_progress and progress: progress.close()




                
            
