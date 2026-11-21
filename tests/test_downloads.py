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
from dracoon.errors import DRACOONCryptoError

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

        return super().setUp()

    async def asyncTearDown(self) -> None:
        await self.dracoon.disconnect()
        self.target_dir.cleanup()

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


if __name__ == '__main__':
    unittest.main()
