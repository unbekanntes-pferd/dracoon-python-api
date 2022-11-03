"""
Async DRACOON downloads adapter based on httpx, tqdm and pydantic
V1.2.0
(c) Octavio Simone, February 2022 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/downloads
Please note: maximum 500 items are returned in GET requests
 - refer to documentation on how to upload files:
https://support.dracoon.com/hc/de/articles/115005512089

"""
import os
from pathlib import Path
import logging
import random
import string

from cryptography.exceptions import InvalidTag
from tqdm import tqdm
import httpx

from dracoon.nodes import CHUNK_SIZE
from dracoon.nodes.models import Callback, Node, NodeType
from dracoon.client import DRACOONClient
from dracoon.crypto import FileDecryptionCipher, decrypt_file_key
from dracoon.crypto.models import FileKey, PlainUserKeyPairContainer
from dracoon.errors import (DRACOONCryptoError, InvalidClientError, ClientDisconnectedError, InvalidFileError, 
                            FileConflictError, InvalidPathError)


class DRACOONDownloads:

    """
    API wrapper for DRACOON uploads endpoint:
    Upload files via proxy upload with given open upload channel.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        
        self.logger = logging.getLogger('dracoon.downloads')
        
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/user'
            
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False

            self.logger.debug("DRACOON downloads adapter created.")
   
        else:
            self.dracoon.logger.critical("DRACOON client not connected.")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    
    def check_file_exists(self, path: str) -> bool:
        """ Check if a file already exists. """

        file = Path(path)

        return file.exists() and file.is_file()

    
    async def download_unencrypted(self, download_url: str, target_path: str, node_info: Node, chunksize: int = CHUNK_SIZE, 
                                   raise_on_err: bool = False, display_progress: bool = False,
                                   callback_fn: Callback  = None,
                                   file_name: str = None
                                   ):
        """ Download a file from an unecrypted data room. """

        self.logger.info("Download started.")
        self.logger.debug("Download to %s", target_path)

        if self.raise_on_err:
            raise_on_err = True
        
        if node_info.type != NodeType.file:
            self.logger.critical("Invalid node type: %s", node_info.type)
            err = InvalidFileError(message='Ony file download possible.')
            await self.dracoon.handle_generic_error(err=err)
        
        if file_name is None:
            file_path = os.path.join(target_path, node_info.name)
        elif file_name is not None:
            file_path = os.path.join(target_path, file_name)
            
        if self.check_file_exists(file_path):
            self.logger.critical("File already exists: %s", file_path)
            err = FileConflictError('File already exists.')
            await self.dracoon.handle_generic_error(err=err)

        folder = Path(target_path)

        if not folder.is_dir():
            self.logger.critical("Target path is not a folder.")
            err = InvalidPathError(f'A folder needs to be provided. {target_path} is not a folder.')
            await self.dracoon.handle_generic_error(err=err)
        
        size = node_info.size
        
        # init callback size
        if callback_fn: callback_fn(0, size)

        self.logger.debug("File download for size: %s", size)
        self.logger.debug("Using chunksize: %s", chunksize)
            
        try:             
            file_out = open(file_path, 'wb')
                
            async with self.dracoon.downloader.stream(method='GET', url=download_url) as res:
                res.raise_for_status()
                if display_progress: progress = tqdm(unit='iMB',unit_divisor=1024, total=size, unit_scale=True, desc=node_info.name)
                async for chunk in res.aiter_bytes(chunksize):
                    file_out.write(chunk)
                    if display_progress: progress.update(len(chunk))
                    if callback_fn: callback_fn(len(chunk))
                                        
        except httpx.RequestError as e:
            os.remove(file_path)
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            os.remove(file_path)
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err, is_xml=True, debug_content=False)
        finally:
            if file_out: file_out.close()
            if display_progress and progress: progress.close()
                   
        self.logger.info("Download completed.")
            

    async def download_encrypted(self, download_url: str, target_path: str, node_info: Node, plain_keypair: PlainUserKeyPairContainer, file_key: FileKey, 
                                       chunksize: int = CHUNK_SIZE, raise_on_err: bool = False, display_progress: bool = False, 
                                       callback_fn: Callback  = None, file_name: str = None):   
        """ Download a file from an encrypted data room. """

        self.logger.info("Download started.")
        self.logger.debug("Download to %s", target_path)

        if self.raise_on_err:
            raise_on_err = True
            
        if not node_info:
            err = InvalidFileError(message='File does not exist.')
            await self.dracoon.handle_generic_error(err=err)
        
        if node_info.type != NodeType.file:
            err = InvalidFileError(message='Ony file download possible.')
            await self.dracoon.handle_generic_error(err=err)

        if file_name is None:
            file_name = node_info.name
  
        folder = Path(target_path)
        
        tmp_filename = self.generate_temporary_filename()
            
        file_path = folder.joinpath(tmp_filename)
            
        if self.check_file_exists(file_path):
            await self.dracoon.logout()
            self.logger.critical("File already exists: %s", file_path)
            err = FileConflictError(message='File already exists.')
            await self.dracoon.handle_generic_error(err=err)

        if not folder.is_dir():
            await self.dracoon.logout()
            self.logger.critical("Target path is not a folder.")
            err = InvalidPathError(f'A file needs to be provided. {target_path} is not a folder.')
            await self.dracoon.handle_generic_error(err=err)
        
        size = node_info.size

        plain_file_key = decrypt_file_key(file_key=file_key, keypair=plain_keypair)
        decryptor = FileDecryptionCipher(plain_file_key=plain_file_key)

        self.logger.debug("File download for size: %s", size)
        self.logger.debug("Using chunksize: %s", chunksize)
        
        # init callback size
        if callback_fn: callback_fn(0, size)

        try:
            with open(file_path, 'wb') as file_out:       
                async with self.dracoon.downloader.stream(method='GET', url=download_url) as res:
                    res.raise_for_status()
                    if display_progress: progress = tqdm(unit='iMB',unit_divisor=1024, total=size, unit_scale=True, desc=node_info.name)   
                        
                    # decrypt file and then write to disk
                    async for chunk in res.aiter_bytes(chunksize):            
                        plain_chunk = decryptor.decode_bytes(chunk)
                        file_out.write(plain_chunk)
                        if display_progress: progress.update(len(chunk))
                        if callback_fn: callback_fn(len(chunk))
                            
                            # finalize encryption after last chunk
                        if not chunk:
                            last_data = decryptor.finalize()
                            file_out.write(last_data)
                                        
                        self.logger.info("Download completed.")
        except InvalidTag:
            # remove unverified decrypted bytes
            os.remove(file_path)
            raise DRACOONCryptoError("Invalid file key")
        except httpx.RequestError as e:
            os.remove(file_path)
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            os.remove(file_path)
            await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err, is_xml=True, debug_content=False)
        finally:
            if display_progress and progress: progress.close()
            
        end_file = folder.joinpath(file_name)
            
        file_path.rename(end_file)
            
    def generate_temporary_filename(self) -> str:
        
        chars = string.ascii_uppercase
        tmp_filename =  ''.join(random.choice(chars) for i in range(12))
        return tmp_filename + '.TMP'
        




                
            
