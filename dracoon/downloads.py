"""
Async DRACOON uploads adapter based on httpx, tqdm and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/uploads
Please note: maximum 500 items are returned in GET requests
 - refer to documentation on how to upload files:
https://support.dracoon.com/hc/de/articles/115005512089

"""

import httpx

from .nodes_models import Node, NodeType
from .crypto_models import FileKey, PlainUserKeyPairContainer
from .core import DRACOONClient
from .crypto import FileDecryptionCipher, decrypt_file_key
from pathlib import Path
import tqdm.asyncio
import os
import logging


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

    
    async def download_unencrypted(self, download_url: str, target_path: str, node_info: Node, chunksize: int = 5242880, raise_on_err: bool = False):
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

        if size < chunksize:
            
            try:
                async with self.dracoon.http.stream(method='GET', url=download_url) as res:

                    file_out = open(file_path, 'wb')

                    async for chunk in tqdm.asyncio.tqdm(iterable=res.aiter_bytes(1024), desc=node_info.name, unit='iKB',unit_scale=True, unit_divisor=1, total=size/1024):
                        file_out.write(chunk)
                        
      
            except httpx.RequestError as e:

                await self.dracoon.handle_connection_error(e)
            except httpx.HTTPStatusError as e:
                await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
            
            file_out.close()
            self.logger.info("Download completed.")
            
        else:
       
            index = 0
            offset = 0
    
            for chunk_range in range(chunksize, size + 1, chunksize):

                offset = index + chunk_range

                content_range = f'bytes={index}-{offset}'
                if offset > size:
                    content_range = f'bytes={index}-{size - 1}'

                self.dracoon.http.headers["Range"] = content_range
                
                try:
                    async with self.dracoon.http.stream(method='GET', url=download_url) as res:
                        
                        res.raise_for_status()
                        file_out = open(file_path, 'wb')
                        desc = node_info["name"] + f' {content_range}'
                        async for chunk in tqdm.asyncio.tqdm(iterable=res.aiter_bytes(1048576), desc=desc, unit='iMB',unit_scale=False, unit_divisor=1024, total=chunksize/1048576):
                            file_out.write(chunk)
                            
                        file_out.close()
                                
                        index = offset + 1

                except httpx.RequestError as e:
                    file_out.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await self.dracoon.handle_connection_error(e)
                except httpx.HTTPStatusError as e:
                    file_out.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
                    
            
            if "range" in self.dracoon.http.headers:
               self.dracoon.http.headers.pop("range")
       
            file_out.close()
            self.logger.info("Download completed.")

        
    async def download_encrypted(self, download_url: str, target_path: str, node_info: Node, plain_keypair: PlainUserKeyPairContainer, file_key: FileKey, 
                                       chunksize: int = 5242880, raise_on_err: bool = False):   
        """ Download a file from an encrypted data room. """

        self.logger.info("Download started.")
        self.logger.debug("Download to %s", target_path)

        if self.raise_on_err:
            raise_on_err = True
        
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

        plain_file_key = decrypt_file_key(fileKey=file_key, keypair=plain_keypair)
        decryptor = FileDecryptionCipher(plain_file_key=plain_file_key)

        self.logger.debug("File download for size: %s", size)
        self.logger.debug("Using chunksize: %s", chunksize)

        if size < chunksize:
            try:
                async with self.dracoon.http.stream(method='GET', url=download_url) as res:
                    res.raise_for_status()
                    file_out = open(file_path, 'wb')

                    async for chunk in tqdm.asyncio.tqdm(iterable=res.aiter_bytes(1048576), desc=node_info.name, unit='iMB',unit_scale=False, unit_divisor=1048576, total=size):
                        
                        plain_chunk = decryptor.decode_bytes(chunk)
                        file_out.write(plain_chunk)
                        if not chunk:
                            last_data = decryptor.finalize()
                            file_out.write(last_data)
                        
                    file_out.close()
                    self.logger.info("Download completed.")

            except httpx.RequestError as e:
                await self.dracoon.handle_connection_error(e)
            except httpx.HTTPStatusError as e:
                await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)



        else:
            index = 0
            offset = 0
    
            for chunk_range in range(chunksize, size + 1, chunksize):

                offset = index + chunk_range

                content_range = f'bytes={index}-{offset}'
                if offset > size:
                    content_range = f'bytes={index}-{size - 1}'

                #print(content_range)
                self.dracoon.http.headers["Range"] = content_range
                try:
                    async with self.dracoon.http.stream(method='GET', url=download_url) as res:
                        
                        res.raise_for_status()
                        file_out = open(file_path, 'wb')
                        desc = node_info["name"] + f' {content_range}'
                        async for chunk in tqdm.asyncio.tqdm(iterable=res.aiter_bytes(1048576), desc=desc, unit='iMB',unit_scale=False, unit_divisor=1024, total=chunksize/1048576):
                            
                            plain_chunk = decryptor.decode_bytes(chunk)
                            file_out.write(plain_chunk)

                            # finalize on last chunk in total
                            if not chunk and (size - offset <= chunksize - 2):
                                last_data = decryptor.finalize()
                                file_out.write(last_data)

                        file_out.close()
                                
                        index = offset + 1
                    
                except httpx.RequestError as e:
                    file_out.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await self.dracoon.handle_connection_error(e)

                except httpx.HTTPStatusError as e:
                    file_out.close()
                    if os.path.exists(file_path):
                        os.remove(file_path)
                    await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

            if "range" in self.dracoon.http.headers:
               self.dracoon.http.headers.pop("range")
       
            self.logger.info("Download completed.")


                
            
