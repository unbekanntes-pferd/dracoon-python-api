from doctest import testfile
import os
import asyncio
from pathlib import Path
import random
import unittest
import dotenv
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import HTTPNotFoundError
from dracoon.nodes import DRACOONNodes, CHUNK_SIZE
from dracoon.nodes.models import Node, TransferJob
from dracoon.nodes.responses import S3FileUploadStatus, S3Status

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')
is_github_action = os.environ.get('IS_GITHUB_ACTION')

chunksize = 1024 * 1024 * 10 # 10 MB to test chunking / S3


class DRACOONTransferTestsHelper():
    def __init__(self, chunksize: int = CHUNK_SIZE, chunks: int = 5):
        self.chunksize = chunksize
        self.chunks = chunks
        self.cwd = Path.cwd()
    
    def generate_small_file(self):
        
        random_int = random.randrange(1000, 10000)
        file_path = Path.joinpath(self.cwd, f'test_small_{random_int}')
        
        with open(file_path, 'wb') as out_file:
            out_file.write(os.urandom(self.chunksize))
            
        return file_path
    
    def generate_large_file(self):
        random_int = random.randrange(1000, 10000)
        file_path = Path.joinpath(self.cwd, f'test_large_{random_int}')
        
        with open(file_path, 'wb') as out_file:
            out_file.write(os.urandom(self.chunksize * self.chunks))
            
        return file_path

@unittest.skipIf(is_github_action is not None, reason="No transfer E2E tests in Github action")  
class TestAsyncDRACOONTransfers(unittest.IsolatedAsyncioTestCase):
    
    async def asyncSetUp(self) -> None:
        asyncio.get_running_loop().set_debug(False)
        
        self.dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
        
        try:
            await self.dracoon.user.get_user_keypair(raise_on_err=True) 
            await self.dracoon.user.delete_user_keypair()
        except HTTPNotFoundError:
            pass
        
        await self.dracoon.user.set_user_keypair('VerySecret123!')
        await self.dracoon.get_keypair('VerySecret123!')
        
        self.test_helper = DRACOONTransferTestsHelper(chunksize=chunksize)
        
        self.assertIsInstance(self.dracoon.nodes, DRACOONNodes)
        self.assertIsInstance(self.dracoon, DRACOON)
        self.assertIsNotNone(self.dracoon.connection)

    async def asyncTearDown(self) -> None:
        await self.dracoon.user.delete_user_keypair()
        await self.dracoon.logout()
        
    async def test_upload_download_small(self):
        test_file = self.test_helper.generate_small_file()
        
        room = self.dracoon.nodes.make_room(name='UPLOAD_TEST_SMALL')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        upload_job = TransferJob()
        file_small = await self.dracoon.upload(target_parent_id=target_node.id, file_path=test_file, callback_fn=upload_job.update_progress)
        self.assertIsInstance(file_small, S3FileUploadStatus)
        self.assertEqual(upload_job.progress, 1)
        self.assertEqual(upload_job.transferred, file_small.node.size)
        self.assertEqual(file_small.status, S3Status.done.value)
        
        download_job = TransferJob()
        download_name = f'{file_small.node.name}_download'
        await self.dracoon.download(target_path=self.test_helper.cwd, callback_fn=download_job.update_progress, 
                                    source_node_id=file_small.node.id, file_name=download_name)
        
        small_file = Path.joinpath(self.test_helper.cwd, download_name)
        self.assertTrue(small_file.exists() and small_file.is_file())
        self.assertEqual(small_file.stat().st_size, file_small.node.size)
        self.assertEqual(download_job.transferred, file_small.node.size)
        self.assertEqual(download_job.progress, 1)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
        os.remove(small_file)
        os.remove(test_file)
        
    async def test_upload_download_large(self):
        test_file = self.test_helper.generate_large_file()
        
        room = self.dracoon.nodes.make_room(name='UPLOAD_TEST_LARGE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        upload_job = TransferJob()
        file_small = await self.dracoon.upload(target_parent_id=target_node.id, file_path=test_file, callback_fn=upload_job.update_progress)
        self.assertIsInstance(file_small, S3FileUploadStatus)
        self.assertEqual(upload_job.progress, 1)
        self.assertEqual(upload_job.transferred, file_small.node.size)
        self.assertEqual(file_small.status, S3Status.done.value)
        
        download_job = TransferJob()
        download_name = f'{file_small.node.name}_download'
        await self.dracoon.download(target_path=self.test_helper.cwd, callback_fn=download_job.update_progress, 
                                    source_node_id=file_small.node.id, file_name=download_name)
        
        small_file = Path.joinpath(self.test_helper.cwd, download_name)
        self.assertTrue(small_file.exists() and small_file.is_file())
        self.assertEqual(small_file.stat().st_size, file_small.node.size)
        self.assertEqual(download_job.transferred, file_small.node.size)
        self.assertEqual(download_job.progress, 1)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
        os.remove(small_file)
        os.remove(test_file)

    async def test_upload_download_small_encrypted(self):
        test_file = self.test_helper.generate_small_file()
        
        room = self.dracoon.nodes.make_room(name='UPLOAD_TEST_SMALL_ENCRYPTED')
        target_node = await self.dracoon.nodes.create_room(room=room)
        encrypt_room = self.dracoon.nodes.make_encrypt_room(is_encrypted=True)
        await self.dracoon.nodes.encrypt_room(room_id=target_node.id, encrypt_room=encrypt_room)
        
        upload_job = TransferJob()
        file_small = await self.dracoon.upload(target_parent_id=target_node.id, file_path=test_file, callback_fn=upload_job.update_progress)
        self.assertIsInstance(file_small, S3FileUploadStatus)
        self.assertEqual(upload_job.progress, 1)
        self.assertEqual(upload_job.transferred, file_small.node.size)
        self.assertEqual(file_small.status, S3Status.done.value)
        
        download_job = TransferJob()
        download_name = f'{file_small.node.name}_download'
        await self.dracoon.download(target_path=self.test_helper.cwd, callback_fn=download_job.update_progress, 
                                    source_node_id=file_small.node.id, file_name=download_name)
        
        small_file = Path.joinpath(self.test_helper.cwd, download_name)
        self.assertTrue(small_file.exists() and small_file.is_file())
        self.assertEqual(small_file.stat().st_size, file_small.node.size)
        self.assertEqual(download_job.transferred, file_small.node.size)
        self.assertEqual(download_job.progress, 1)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
        os.remove(small_file)
        os.remove(test_file)
    
    async def test_upload_download_large_encrypted(self):
        test_file = self.test_helper.generate_large_file()
        
        room = self.dracoon.nodes.make_room(name='UPLOAD_TEST_LARGE_ENCRYPTED')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        encrypt_room = self.dracoon.nodes.make_encrypt_room(is_encrypted=True)
        await self.dracoon.nodes.encrypt_room(room_id=target_node.id, encrypt_room=encrypt_room)
        
        upload_job = TransferJob()
        file_small = await self.dracoon.upload(target_parent_id=target_node.id, file_path=test_file, callback_fn=upload_job.update_progress)
        self.assertIsInstance(file_small, S3FileUploadStatus)
        self.assertEqual(upload_job.progress, 1)
        self.assertEqual(upload_job.transferred, file_small.node.size)
        self.assertEqual(file_small.status, S3Status.done.value)
        
        download_job = TransferJob()
        download_name = f'{file_small.node.name}_download'
        await self.dracoon.download(target_path=self.test_helper.cwd, callback_fn=download_job.update_progress, 
                                    source_node_id=file_small.node.id, file_name=download_name)
        
        small_file = Path.joinpath(self.test_helper.cwd, download_name)
        self.assertTrue(small_file.exists() and small_file.is_file())
        self.assertEqual(small_file.stat().st_size, file_small.node.size)
        self.assertEqual(download_job.transferred, file_small.node.size)
        self.assertEqual(download_job.progress, 1)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
        os.remove(small_file)
        os.remove(test_file)

    async def test_upload_custom_filename(self):
        test_file = self.test_helper.generate_small_file()
        
        room = self.dracoon.nodes.make_room(name='UPLOAD_TEST_SMALL_FILENAME')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        upload_job = TransferJob()
        file_small = await self.dracoon.upload(target_parent_id=target_node.id, file_path=test_file, callback_fn=upload_job.update_progress, file_name='othername.test')
        self.assertIsInstance(file_small, S3FileUploadStatus)
        self.assertEqual(upload_job.progress, 1)
        self.assertEqual(upload_job.transferred, file_small.node.size)
        self.assertEqual(file_small.status, S3Status.done.value)
        self.assertNotEqual(file_small.node.name, test_file.name)
        self.assertEqual(file_small.node.name, 'othername.test')
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
        os.remove(test_file)

       
if __name__ == '__main__':
    unittest.main()
