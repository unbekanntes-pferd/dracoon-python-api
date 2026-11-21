import unittest
import tempfile
from pathlib import Path
from datetime import datetime

import respx

from dracoon.client import DRACOONClient
from dracoon.client.models import DRACOONConnection
from dracoon.downloads import DRACOONDownloads
from dracoon.nodes.models import Node, NodeType
from dracoon.crypto import create_plain_userkeypair, create_file_key, encrypt_bytes, encrypt_file_key
from dracoon.crypto.models import UserKeyPairVersion
from dracoon.errors import DRACOONCryptoError, FileConflictError, InvalidPathError, HTTPNotFoundError

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
DOWNLOAD_URL = 'https://dracoon.team/not/real/download_url'
PLAIN_DATA = b'DRACOON encrypted download test payload ' * 64


class TestAsyncDRACOONDownloads(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.plain_keypair = create_plain_userkeypair(version=UserKeyPairVersion.RSA2048)

    def setUp(self) -> None:
        self.dracoon = DRACOONClient(base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        self.dracoon.connection = DRACOONConnection(datetime.now(), 'access_token', 3600, 'refresh_token')
        self.downloads = DRACOONDownloads(self.dracoon)

        self.target_dir = tempfile.TemporaryDirectory()
        self.target_path = Path(self.target_dir.name)

        enc_data, plain_file_key = encrypt_bytes(plain_data=PLAIN_DATA, plain_file_key=create_file_key())
        self.enc_data = enc_data
        self.file_key = encrypt_file_key(plain_file_key=plain_file_key, keypair=self.plain_keypair)
        self.node = Node.model_construct(id=1, name='test.bin', type=NodeType.file, size=len(enc_data), isEncrypted=True)
        self.plain_node = Node.model_construct(id=1, name='test.bin', type=NodeType.file, size=len(PLAIN_DATA), isEncrypted=False)

        return super().setUp()

    async def asyncTearDown(self) -> None:
        await self.dracoon.disconnect()
        self.target_dir.cleanup()

    @respx.mock
    async def test_download_unencrypted(self):
        download_mock = respx.get(DOWNLOAD_URL).respond(200, content=PLAIN_DATA)
        progress = []

        await self.downloads.download_unencrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.plain_node,
                                                  chunksize=256, callback_fn=lambda val, total=None: progress.append((val, total)))

        assert download_mock.called
        assert self.target_path.joinpath('test.bin').read_bytes() == PLAIN_DATA
        assert progress[0] == (0, len(PLAIN_DATA))
        assert sum(val for val, _ in progress) == len(PLAIN_DATA)

    @respx.mock
    async def test_download_unencrypted_custom_file_name(self):
        respx.get(DOWNLOAD_URL).respond(200, content=PLAIN_DATA)

        await self.downloads.download_unencrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.plain_node,
                                                  file_name='renamed.bin')

        assert [file.name for file in self.target_path.iterdir()] == ['renamed.bin']

    async def test_download_unencrypted_existing_file(self):
        self.target_path.joinpath('test.bin').write_bytes(b'existing')

        with self.assertRaises(FileConflictError):
            await self.downloads.download_unencrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.plain_node)

        assert self.target_path.joinpath('test.bin').read_bytes() == b'existing'

    async def test_download_unencrypted_target_not_a_folder(self):
        target_file = self.target_path.joinpath('not_a_folder')
        target_file.write_bytes(b'')

        with self.assertRaises(InvalidPathError):
            await self.downloads.download_unencrypted(download_url=DOWNLOAD_URL, target_path=str(target_file), node_info=self.plain_node)

    @respx.mock
    async def test_download_unencrypted_http_error(self):
        respx.get(DOWNLOAD_URL).respond(404)
        self.downloads.raise_on_err = True

        with self.assertRaises(HTTPNotFoundError):
            await self.downloads.download_unencrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.plain_node)

        assert list(self.target_path.iterdir()) == []

    @respx.mock
    async def test_download_encrypted(self):
        download_mock = respx.get(DOWNLOAD_URL).respond(200, content=self.enc_data)

        await self.downloads.download_encrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.node,
                                                plain_keypair=self.plain_keypair, file_key=self.file_key, chunksize=256)

        assert download_mock.called
        assert [file.name for file in self.target_path.iterdir()] == ['test.bin']
        assert self.target_path.joinpath('test.bin').read_bytes() == PLAIN_DATA

    @respx.mock
    async def test_download_encrypted_tampered_data(self):
        tampered_data = bytearray(self.enc_data)
        tampered_data[5] ^= 0xFF
        respx.get(DOWNLOAD_URL).respond(200, content=bytes(tampered_data))

        with self.assertRaises(DRACOONCryptoError):
            await self.downloads.download_encrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.node,
                                                    plain_keypair=self.plain_keypair, file_key=self.file_key, chunksize=256)

        # unverified plain bytes must not be left on disk
        assert list(self.target_path.iterdir()) == []

    @respx.mock
    async def test_download_encrypted_existing_file(self):
        download_mock = respx.get(DOWNLOAD_URL).respond(200, content=self.enc_data)
        self.target_path.joinpath('test.bin').write_bytes(b'existing')

        with self.assertRaises(FileConflictError):
            await self.downloads.download_encrypted(download_url=DOWNLOAD_URL, target_path=self.target_dir.name, node_info=self.node,
                                                    plain_keypair=self.plain_keypair, file_key=self.file_key)

        assert self.target_path.joinpath('test.bin').read_bytes() == b'existing'
        assert [file.name for file in self.target_path.iterdir()] == ['test.bin']
        assert not download_mock.called
        # validation errors must not end the session
        assert self.dracoon.connection is not None

    async def test_download_encrypted_target_not_a_folder(self):
        target_file = self.target_path.joinpath('not_a_folder')
        target_file.write_bytes(b'')

        with self.assertRaises(InvalidPathError):
            await self.downloads.download_encrypted(download_url=DOWNLOAD_URL, target_path=str(target_file), node_info=self.node,
                                                    plain_keypair=self.plain_keypair, file_key=self.file_key)

        assert self.dracoon.connection is not None


if __name__ == '__main__':
    unittest.main()
