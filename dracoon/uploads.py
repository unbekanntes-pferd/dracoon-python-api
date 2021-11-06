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
from dracoon.crypto_models import PlainUserKeyPairContainer
from .core import DRACOONClient
from .crypto import FileEncryptionCipher, encrypt_bytes, encrypt_file_key, create_file_key, get_file_key_version
from .uploads_models import FinalizeUpload, UploadChannelResponse
from pydantic import validate_arguments, HttpUrl
from pathlib import Path
import os
from tqdm import tqdm


class DRACOONUploads:

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
        else:
            raise ValueError(
                'DRACOON client must be connected: client.connect()')

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
                                 keep_shares: bool = False, resolution_strategy: str = 'autorename', chunksize: int = 5242880):
        """ uploads a file to an unencrypted data room – upload channel required """
        file = Path(file_path)
        
        if not file.is_file():
            raise ValueError(f'A file needs to be provided. {file_path} is not a file.')
        
        filesize = os.stat(file_path).st_size
        file_name = file_path.split('/')[-1]

        if filesize < chunksize:
            progress = tqdm(unit='iB',unit_divisor=1024, total=filesize, unit_scale=True)
            file_obj = open(file, 'rb')

            try:
                res = await self.dracoon.http.post(url=upload_channel["uploadUrl"], data=self.upload_bytes(file_obj))
                res.raise_for_status()
                progress.update(filesize)
            except httpx.RequestError as e:
                res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
            except httpx.HTTPStatusError as e:
                res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                raise ValueError(f'Upload failed: {e.response.status_code} – {e.response.text}')
            finally:
                progress.close()
         
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

                    offset = index + len(chunk)
                    index = offset

                    self.dracoon.http.headers["Content-Range"] = content_range


                    try:
                        res = await self.dracoon.http.post(url=upload_channel["uploadUrl"], files=upload_file)
                        res.raise_for_status()
                        progress.update(len(chunk))
                    except httpx.RequestError as e:
                        res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                        raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
                    except httpx.HTTPStatusError as e:
                        res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                        raise ValueError(f'Upload failed: {e.response.status_code} – {e.response.text}')


                progress.close()
                    
                                
        api_url = self.dracoon.base_url + self.dracoon.api_base_url + f'/uploads/{upload_channel["token"]}'

        params = {
                "resolutionStrategy": resolution_strategy,
                "keepShareLinks": keep_shares,
                "fileName": file_name
            }

        try:
            res = await self.dracoon.http.put(api_url, json=params)
        except httpx.RequestError as e:
                raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')


        if "content-range" in self.dracoon.http.headers:
            self.dracoon.http.headers.pop("content-range")
                
        return res
                

    async def upload_encrypted(self, file_path: str, upload_channel: UploadChannelResponse, user_id: int, plain_keypair: PlainUserKeyPairContainer, 
                            keep_shares: bool = False, resolution_strategy: str = 'autorename', chunksize: int = 5242880):
        """ uploads a file to an encrypted data room – upload channel and plain user keypair required """
        file = Path(file_path)
        if not file.is_file():
            raise ValueError(f'A file needs to be provided. {file_path} is not a file.')

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
                res = await self.dracoon.http.post(url=upload_channel["uploadUrl"], files=files)
                res.raise_for_status()
                progress.update(filesize)
            except httpx.RequestError as e:
                raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
            except httpx.HTTPStatusError as e:
                res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                raise ValueError(f'Upload failed: {e.response.status_code} – {e.response.text}')
            finally:
                progress.close()

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
                        res = await self.dracoon.http.post(upload_channel["uploadUrl"], files=upload_file)
                        res.raise_for_status()
                        progress.update(len(chunk))
                    except httpx.RequestError as e:
                        progress.close()
                        raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')
                    except httpx.HTTPStatusError as e:
                        progress.close()
                        res = await self.dracoon.http.delete(upload_channel["uploadUrl"])
                        raise ValueError(f'Upload failed: {e.response.status_code} – {e.response.text}')

            progress.close()
                        
        api_url = self.dracoon.base_url + self.dracoon.api_base_url + f'/uploads/{upload_channel["token"]}'

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
        except httpx.RequestError as e:
                raise httpx.RequestError(f'Connection to DRACOON failed: {e.request.url}')

        if "content-range" in self.dracoon.http.headers:
            self.dracoon.http.headers.pop("content-range")
                
        return res


                
"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# upload a file (step 2 of file upload process - to generate an upload url, use nodes.create_upload_channel)


@validate_arguments
def upload_file(uploadURL: HttpUrl, upload_file, content_range: str, content_length: str):
    api_call = {
        'url': uploadURL,
        'files': upload_file,
        'method': 'POST'
    }
    if content_range != None:
        api_call["Content-Range"] = content_range
    if content_length != None:
        api_call["Content-Length"] = content_length
    return api_call

# finalie upload - body/params must be empty for public


@validate_arguments
def finalize_upload(uploadURL: HttpUrl, params: FinalizeUpload = None):
    api_call = {
        'url': uploadURL,
        'files': None,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    if params != None:
        api_call["body"] = params

    return api_call

# delete upload request


@validate_arguments
def cancel_upload(uploadURL: HttpUrl):
    api_call = {
        'url': uploadURL,
        'files': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call


        


