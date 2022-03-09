
import logging
from dracoon.nodes_responses import S3FileUploadStatus, Webhook
from dracoon.settings import DRACOONSettings
from dracoon import DRACOON, OAuth2ConnectionType
import dotenv
import os
import shutil
import asyncio
from pathlib import Path



dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

upload_target = os.environ.get('E2E_UPLOAD_TARGET')
upload_crypto_target = os.environ.get('E2E_CRYPTO_UPLOAD_TARGET')
upload_file_small = os.environ.get('E2E_UPLOAD_SOURCE_SMALL')
upload_file_large = os.environ.get('E2E_UPLOAD_SOURCE_LARGE')

download_target = os.environ.get('E2E_DOWNLOAD_TARGET')

async def test_transfers_e2e():
    dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    
    await dracoon.user.set_user_keypair('VerySecret123!')
    
    await dracoon.get_keypair('VerySecret123!')
    
    file_small = await dracoon.upload(target_path=upload_target, file_path=upload_file_small)
    assert isinstance(file_small, S3FileUploadStatus)
    print('Uploading small file (no chunking) test passed (/)')
    
    
    file_large = await dracoon.upload(target_path=upload_target, file_path=upload_file_large, display_progress=True)
    assert isinstance(file_large, S3FileUploadStatus)
    print('Uploading large file (chunking) test passed (/)')
    

    crypto_file_small = await dracoon.upload(target_path=upload_crypto_target, file_path=upload_file_small)
    assert isinstance(crypto_file_small, S3FileUploadStatus)
    print('Uploading small file (no chunking, encrypted) test passed (/)')
    
    
    crypto_file_large = await dracoon.upload(target_path=upload_crypto_target, file_path=upload_file_large, display_progress=True)
    assert isinstance(crypto_file_large, S3FileUploadStatus)
    print('Uploading large file (chunking, encrypted) test passed (/)')
    
    tmp_dir = os.path.join(download_target, 'e2etest')
    crypto_tmp_dir = os.path.join(download_target, 'e2etest_crypto')
    
    os.mkdir(path=tmp_dir)
    os.mkdir(path=crypto_tmp_dir)
    
    download_path_small = file_small.node.parentPath + f'{file_small.node.name}'
    download_path_large = file_large.node.parentPath + f'{file_large.node.name}'
    
    crypto_download_path_small = crypto_file_small.node.parentPath + f'{crypto_file_small.node.name}'
    crypto_download_path_large = crypto_file_large.node.parentPath + f'{crypto_file_large.node.name}'
    
    await dracoon.download(file_path=download_path_small, target_path=tmp_dir)
    
    small_file = Path(os.path.join(tmp_dir, file_small.node.name))
    assert small_file.exists() and small_file.is_file() 
    assert os.stat(os.path.join(tmp_dir, file_small.node.name)).st_size == file_small.node.size
    
    print('Downloading small file (no chunking) test passed (/)')
    
    await dracoon.download(file_path=download_path_large, target_path=tmp_dir, display_progress=True)
    
    large_file = Path(os.path.join(tmp_dir, file_large.node.name))
    assert large_file.exists() and large_file.is_file() 
    assert os.stat(os.path.join(tmp_dir, file_large.node.name)).st_size == file_large.node.size
    
    print('Downloading large file (no chunking, stream) test passed (/)')
    
    await dracoon.download(file_path=crypto_download_path_small, target_path=crypto_tmp_dir)
    
    small_crypto_file = Path(os.path.join(crypto_tmp_dir, crypto_file_small.node.name))
    assert small_crypto_file.exists() and small_crypto_file.is_file() 
    assert os.stat(os.path.join(crypto_tmp_dir, crypto_file_small.node.name)).st_size == crypto_file_small.node.size
    
    print('Downloading small file (no chunking, encrypted) test passed (/)')
    
    await dracoon.download(file_path=crypto_download_path_large, target_path=crypto_tmp_dir, display_progress=True)
    
    large_crypto_file = Path(os.path.join(crypto_tmp_dir, crypto_file_large.node.name))
    assert large_crypto_file.exists() and large_crypto_file.is_file() 
    assert os.stat(os.path.join(crypto_tmp_dir, crypto_file_large.node.name)).st_size == crypto_file_large.node.size
    
    print('Downloading large file (chunking, encrypted) test passed (/)')
    
    try:
        shutil.rmtree(tmp_dir)
        shutil.rmtree(crypto_tmp_dir)
    except OSError as e:
        print("Could not delete test folder.")
        
    await dracoon.user.delete_user_keypair()
    await dracoon.logout()
        
    print('Down- and upload (transfers) tests passed (/)')
        
if __name__ == '__main__':
    asyncio.run(test_transfers_e2e())
