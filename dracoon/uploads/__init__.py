"""
Async DRACOON uploads adapter based on httpx, tqdm and pydantic
V1.2.0
(c) Octavio Simone, November 2021 

Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/uploads
Please note: maximum 500 items are returned in GET requests
 - refer to documentation on how to upload files:
https://support.dracoon.com/hc/de/articles/115005512089

"""

from typing import List
from pathlib import Path
import os
import logging


from tqdm import tqdm

from dracoon.crypto.models import PlainUserKeyPairContainer
from dracoon.client import DRACOONClient
from dracoon.crypto import FileEncryptionCipher, encrypt_bytes, encrypt_file_key, create_file_key, get_file_key_version
from dracoon.errors import ClientDisconnectedError, InvalidClientError, InvalidFileError
from .models import UploadChannelResponse


class DRACOONUploads:

    """
    API wrapper for DRACOON uploads endpoint:
    Upload files via proxy upload with given open upload channel.
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise InvalidClientError(message='Invalid client.')
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/user'
            self.logger = logging.getLogger('dracoon.uploads')
            if self.dracoon.raise_on_err:
                self.raise_on_err = True
            else:
                self.raise_on_err = False
            self.logger.debug("DRACOON uploads adapter created.")
        else:
            self.logger.error("DRACOON client error: no connection. ")
            raise ClientDisconnectedError(message='DRACOON client must be connected: client.connect()')

    def read_in_chunks(self, file_obj, chunksize = 5242880):
        """ iterator to read a file object in chunks (default chunk size: 5 MB) """
        while True:
            data = file_obj.read(chunksize)
            if not data:
                break
            yield data


    async def upload_bytes(self, file_obj):
        """ async iterator to stream byte upload """
        while True:
            data = file_obj.read()
            if not data:
                break
            yield data


    async def upload_unencrypted(self, file_path: str, upload_channel: UploadChannelResponse, 
                                 keep_shares: bool = False, resolution_strategy: str = 'autorename', chunksize: int = 33554432, raise_on_err: bool = False):
        """ uploads a file to an unencrypted data room – upload channel required """

        if self.raise_on_err:
            raise_on_err = True

        """ Check if file is file """

        file = Path(file_path)
        
        if not file.is_file():
            self.logger.critical('File not found: %s', file_path)
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err=err)
        
        filesize = os.stat(file_path).st_size
        file_name = file_path.split('/')[-1]


        """ Single request upload  """

        if filesize < chunksize:
            progress = tqdm(unit='iMB',unit_divisor=1024, total=filesize, unit_scale=True)
            file_obj = open(file, 'rb')

            try:
                res = await self.dracoon.http.post(url=upload_channel.uploadUrl, data=self.upload_bytes(file_obj))
                res.raise_for_status()
                progress.update(filesize)
            except httpx.RequestError as e:
                res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                await self.dracoon.handle_connection_error(e)
            except httpx.HTTPStatusError as e:
                self.logger.error("Uploading file failed.")
                res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)
            finally:
                progress.close()
        
            """ Chunked upload """
   
        else:
            with open(file, 'rb') as f:

                index = 0
                offset = 0

                progress = tqdm(unit='iB',unit_divisor=1024, total=filesize, unit_scale=True)
                for chunk in self.read_in_chunks(f, chunksize):


                    content_range = f'bytes {index}-{offset}/{filesize}'

                    upload_file = {
                    'file': chunk
                        }

                    
                    index = offset

                    self.dracoon.http.headers["Content-Range"] = content_range


                    try:
                        res = await self.dracoon.http.post(url=upload_channel.uploadUrl, files=upload_file)
                        res.raise_for_status()
                        progress.update(len(chunk))
                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_connection_error(e)
                    except httpx.HTTPStatusError as e:
                        self.logger.error("Uploading chunk failed.")
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_http_error(err=e, raise_on_err=raise_on_err)

                progress.close()
                
        """ Finalizing file upload with last PUT """
                                
        api_url = self.dracoon.base_url + self.dracoon.api_base_url + f'/uploads/{upload_channel.token}'

        params = {
                "resolutionStrategy": resolution_strategy,
                "keepShareLinks": keep_shares,
                "fileName": file_name
            }

        try:
            res = await self.dracoon.http.put(api_url, json=params)
            res.raise_for_status()

        except httpx.RequestError as e:
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Finalizing upload failed.")
            await self.dracoon.handle_http_error(e, raise_on_err)


        if "content-range" in self.dracoon.http.headers:
            self.dracoon.http.headers.pop("content-range")
        
        self.logger.info("Uploaded file.")
        return res
                
    async def upload_encrypted(self, file_path: str, upload_channel: UploadChannelResponse, user_id: int, plain_keypair: PlainUserKeyPairContainer, 
                            keep_shares: bool = False, resolution_strategy: str = 'autorename', chunksize: int = 5242880, raise_on_err: bool = False):
        """ uploads a file to an encrypted data room – upload channel and plain user keypair required """

        if self.raise_on_err:
            raise_on_err = True

        file = Path(file_path)
        if not file.is_file():
            self.logger.critical('File not found: %s', file_path)
            err = InvalidFileError(message=f'A file needs to be provided. {file_path} is not a file.')
            await self.dracoon.handle_generic_error(err=err)

        filesize = os.stat(file_path).st_size 
        file_name = file_path.split('/')[-1]

        # no chunking, encrypt on the fly
        if filesize < chunksize:
            progress = tqdm(unit='iB',unit_divisor=1024, total=filesize, unit_scale=True)
            version = get_file_key_version(plain_keypair)

            plain_file_key = create_file_key(version)

            buffer = open(file, 'rb').read()

            enc_buffer, plain_file_key = encrypt_bytes(buffer, plain_file_key)


            files = {
              "file": enc_buffer
            }


            try:
                res = await self.dracoon.http.post(url=upload_channel.uploadUrl, files=files)
                res.raise_for_status()
                progress.update(filesize)
            except httpx.RequestError as e:
                res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                await self.dracoon.handle_connection_error(e)
            except httpx.HTTPStatusError as e:
                res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                self.logger.error("Finalizing upload failed.")
                await self.dracoon.handle_http_error(e, raise_on_err)
            finally:
                progress.close()
            
            self.logger.info("Uploaded file.")

        #  file size larger than chunk size
        else:
            
            version = get_file_key_version(plain_keypair)

            plain_file_key = create_file_key(version)
            dracoon_cipher = FileEncryptionCipher(plain_file_key=plain_file_key)

            with open(file, 'rb') as f:

                index = 0
                offset = 0
                progress = tqdm(unit='B',unit_divisor=1024, total=filesize, unit_scale=True)
                for chunk in self.read_in_chunks(f, chunksize):

                    content_range = f'bytes {index}-{offset}/{filesize}'
          
                    
                    # if not las chunk
                    if filesize - offset > chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                    
                    # last chunk needs to include the final data 
                    elif filesize - offset <= chunksize:
                        enc_chunk = dracoon_cipher.encode_bytes(chunk)
                        last_chunk, plain_file_key = dracoon_cipher.finalize() 
                        enc_chunk += last_chunk

                    upload_file = {
                           'file': enc_chunk
                                }

                    offset = index + len(enc_chunk)
                    index = offset
                    self.dracoon.http.headers["Content-Range"] = content_range

                    try:      
                        res = await self.dracoon.http.post(upload_channel.uploadUrl, files=upload_file)
                        res.raise_for_status()
                        progress.update(len(chunk))
                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        await self.dracoon.handle_connection_error(e)
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel.uploadUrl)
                        self.logger.error("Uploading chunk failed.")

            progress.close()
                        
        api_url = self.dracoon.base_url + self.dracoon.api_base_url + f'/uploads/{upload_channel.token}'

        enc_file_key = encrypt_file_key(plain_file_key=plain_file_key, keypair=plain_keypair)

        params = {
                "resolutionStrategy": resolution_strategy,
                "keepShareLinks": keep_shares,
                "fileName": file_name,
                "fileKey": enc_file_key,
                "userFileKeyList": { 
                    "items": [
                    {
                    "fileKey": enc_file_key,
                    "userId": user_id
                    }
                ]
                }
            }

        try:
            res = await self.dracoon.http.put(api_url, json=params)
            res.raise_for_status()
        except httpx.RequestError as e:
            res = await self.dracoon.http.delete(upload_channel.uploadUrl)
            await self.dracoon.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.error("Finalizing upload failed.")
            res = await self.dracoon.http.delete(upload_channel.uploadUrl)
            await self.dracoon.handle_http_error(e, self.raise_on_err)

        if "content-range" in self.dracoon.http.headers:
            self.dracoon.http.headers.pop("content-range")
        
        self.logger.info("Uploaded file.")
        return res