import unittest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import httpx

from dracoon import DRACOON
from dracoon.client.models import DRACOONConnection
from dracoon.nodes import DRACOONNodes, MIN_CHUNK_SIZE
from dracoon.nodes.models import Node, NodeType
from dracoon.nodes.responses import CreateFileUploadResponse, DownloadTokenGenerateResponse
from dracoon.downloads import DRACOONDownloads
from dracoon.user import DRACOONUser
from dracoon.crypto import create_plain_userkeypair, encrypt_private_key
from dracoon.crypto.models import FileKey, UserKeyPairVersion
from dracoon.errors import (CryptoMissingKeypairError, CryptoMissingFileKeyError, DRACOONCryptoError, HTTPNotFoundError,
                            InvalidPathError, ClientDisconnectedError)

BASE_URL = 'https://dracoon.team'
DOWNLOAD_URL = 'https://dracoon.team/not/real/download_url'
UPLOAD_METHODS = ['upload_unencrypted', 'upload_encrypted', 'upload_s3_unencrypted', 'upload_s3_encrypted']


def make_node(is_encrypted: bool) -> Node:
    return Node.model_construct(id=2, name='test.bin', type=NodeType.file, size=8, isEncrypted=is_encrypted)


class TestAsyncDRACOON(unittest.IsolatedAsyncioTestCase):
    """ routing of DRACOON.upload() / DRACOON.download() to the transfer implementations """

    @classmethod
    def setUpClass(cls) -> None:
        cls.plain_keypair = create_plain_userkeypair(version=UserKeyPairVersion.RSA2048)

    def setUp(self) -> None:
        self.dracoon = DRACOON(base_url=BASE_URL)
        self.dracoon.client.connection = DRACOONConnection(datetime.now(), 'access_token', 3600, 'refresh_token')
        self.dracoon.client.connected = True
        self.dracoon.system_info = SimpleNamespace(useS3Storage=False)

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.file_path = Path(self.tmp_dir.name).joinpath('test.bin')
        self.file_path.write_bytes(b'testdata')

        return super().setUp()

    async def asyncTearDown(self) -> None:
        await self.dracoon.client.disconnect()
        self.tmp_dir.cleanup()

    def unlock_keypair(self):
        self.dracoon.plain_keypair = self.plain_keypair
        self.dracoon.user_info = SimpleNamespace(id=1)

    def patch_nodes(self, target_node: Node):
        """ patch node lookup, upload channel and all upload implementations """
        mocks = {method: AsyncMock(return_value=None) for method in UPLOAD_METHODS}
        mocks['get_node_from_path'] = AsyncMock(return_value=target_node)
        mocks['get_node'] = AsyncMock(return_value=target_node)
        mocks['create_upload_channel'] = AsyncMock(
            return_value=CreateFileUploadResponse(uploadUrl=f'{BASE_URL}/api/v4/uploads/token', uploadId='upload_id', token='token'))
        mocks['get_download_url'] = AsyncMock(return_value=DownloadTokenGenerateResponse(downloadUrl=DOWNLOAD_URL))
        mocks['get_user_file_key'] = AsyncMock(return_value=FileKey(key='key', iv='iv', version='A', tag='tag'))
        return patch.multiple(DRACOONNodes, **mocks), mocks

    # uploads

    async def test_upload_routing(self):
        cases = {
            (False, False): 'upload_unencrypted',
            (False, True): 'upload_encrypted',
            (True, False): 'upload_s3_unencrypted',
            (True, True): 'upload_s3_encrypted',
        }
        self.unlock_keypair()
        for (use_s3, is_encrypted), expected_method in cases.items():
            with self.subTest(use_s3=use_s3, is_encrypted=is_encrypted):
                self.dracoon.system_info.useS3Storage = use_s3
                patcher, mocks = self.patch_nodes(make_node(is_encrypted))
                with patcher:
                    await self.dracoon.upload(file_path=str(self.file_path), target_path='/room/')

                mocks['get_node_from_path'].assert_awaited_once_with(path='/room/', raise_on_err=False)
                upload_channel = mocks['create_upload_channel'].call_args.kwargs['upload_channel']
                assert upload_channel.parentId == 2
                assert upload_channel.name == 'test.bin'
                assert upload_channel.directS3Upload == use_s3
                for method in UPLOAD_METHODS:
                    assert mocks[method].await_count == (1 if method == expected_method else 0), method
                assert mocks[expected_method].call_args.kwargs['file_path'] == str(self.file_path)

    async def test_upload_s3_enforces_min_chunksize(self):
        self.dracoon.system_info.useS3Storage = True
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=False))
        with patcher:
            await self.dracoon.upload(file_path=str(self.file_path), target_path='/room/', chunksize=1024)

        assert mocks['upload_s3_unencrypted'].call_args.kwargs['chunksize'] == MIN_CHUNK_SIZE

    async def test_upload_proxy_keeps_chunksize(self):
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=False))
        with patcher:
            await self.dracoon.upload(file_path=str(self.file_path), target_path='/room/', chunksize=1024)

        assert mocks['upload_unencrypted'].call_args.kwargs['chunksize'] == 1024

    async def test_upload_target_parent_id(self):
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=False))
        with patcher:
            await self.dracoon.upload(file_path=str(self.file_path), target_parent_id=2)

        mocks['get_node'].assert_awaited_once_with(node_id=2, raise_on_err=False)
        assert not mocks['get_node_from_path'].called

    async def test_upload_encrypted_without_keypair(self):
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=True))
        with patcher:
            with self.assertRaises(CryptoMissingKeypairError):
                await self.dracoon.upload(file_path=str(self.file_path), target_path='/room/')

        for method in UPLOAD_METHODS:
            assert not mocks[method].called

    async def test_upload_missing_target(self):
        patcher, _ = self.patch_nodes(make_node(is_encrypted=False))
        with patcher:
            with self.assertRaises(InvalidPathError):
                await self.dracoon.upload(file_path=str(self.file_path))

    async def test_upload_target_not_found(self):
        patcher, _ = self.patch_nodes(None)
        with patcher:
            with self.assertRaises(InvalidPathError):
                await self.dracoon.upload(file_path=str(self.file_path), target_path='/missing/')

    # downloads

    async def test_download_unencrypted(self):
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=False))
        with patcher, patch.object(DRACOONDownloads, 'download_unencrypted', new_callable=AsyncMock) as download_mock:
            await self.dracoon.download(file_path='/room/test.bin', target_path=self.tmp_dir.name)

        mocks['get_node_from_path'].assert_awaited_once_with(path='/room/test.bin', raise_on_err=False)
        mocks['get_download_url'].assert_awaited_once_with(node_id=2, raise_on_err=False)
        assert download_mock.call_args.kwargs['download_url'] == DOWNLOAD_URL
        assert download_mock.call_args.kwargs['target_path'] == self.tmp_dir.name

    async def test_download_encrypted(self):
        self.unlock_keypair()
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=True))
        with patcher, patch.object(DRACOONDownloads, 'download_encrypted', new_callable=AsyncMock) as download_mock:
            await self.dracoon.download(source_node_id=2, target_path=self.tmp_dir.name)

        mocks['get_node'].assert_awaited_once_with(node_id=2)
        mocks['get_user_file_key'].assert_awaited_once()
        assert download_mock.call_args.kwargs['file_key'].key == 'key'
        assert download_mock.call_args.kwargs['plain_keypair'] == self.plain_keypair

    async def test_download_encrypted_without_keypair(self):
        patcher, _ = self.patch_nodes(make_node(is_encrypted=True))
        with patcher, patch.object(DRACOONDownloads, 'download_encrypted', new_callable=AsyncMock) as download_mock:
            with self.assertRaises(CryptoMissingKeypairError):
                await self.dracoon.download(file_path='/room/test.bin', target_path=self.tmp_dir.name)

        assert not download_mock.called

    async def test_download_encrypted_missing_file_key(self):
        self.unlock_keypair()
        request = httpx.Request('GET', BASE_URL)
        not_found = HTTPNotFoundError(error=httpx.HTTPStatusError('error', request=request, response=httpx.Response(404, request=request)))
        patcher, mocks = self.patch_nodes(make_node(is_encrypted=True))
        mocks['get_user_file_key'].side_effect = not_found
        with patcher:
            with self.assertRaises(CryptoMissingFileKeyError):
                await self.dracoon.download(file_path='/room/test.bin', target_path=self.tmp_dir.name)

    async def test_download_not_connected(self):
        self.dracoon.client.connection = None
        with self.assertRaises(ClientDisconnectedError):
            await self.dracoon.download(file_path='/room/test.bin', target_path=self.tmp_dir.name)

    # connection

    async def test_valid_access_token(self):
        assert await self.dracoon.valid_access_token() is True

        self.dracoon.client.connection = DRACOONConnection(datetime.now() - timedelta(hours=2), 'access_token', 3600, 'refresh_token')
        assert await self.dracoon.valid_access_token() is False

    # keypair

    async def test_get_keypair(self):
        enc_keypair = encrypt_private_key('secret', self.plain_keypair)
        with patch.object(DRACOONUser, 'get_user_keypair', new=AsyncMock(return_value=enc_keypair)):
            plain_keypair = await self.dracoon.get_keypair(secret='secret')

        assert plain_keypair.publicKeyContainer.publicKey == self.plain_keypair.publicKeyContainer.publicKey
        assert self.dracoon.plain_keypair == plain_keypair

    async def test_get_keypair_wrong_secret(self):
        enc_keypair = encrypt_private_key('secret', self.plain_keypair)
        with patch.object(DRACOONUser, 'get_user_keypair', new=AsyncMock(return_value=enc_keypair)):
            with self.assertRaises(DRACOONCryptoError):
                await self.dracoon.get_keypair(secret='wrong secret')

        assert self.dracoon.plain_keypair is None


if __name__ == '__main__':
    unittest.main()
