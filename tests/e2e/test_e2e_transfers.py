from dracoon.nodes import MIN_CHUNK_SIZE

from tests.e2e.harness import E2ECryptoTestCase, E2ETestCase

# smallest chunk size valid for both storage types (S3 requires 5 MB parts) - 2.5 chunks: partial last chunk
MULTI_CHUNK_SIZE = MIN_CHUNK_SIZE * 2 + MIN_CHUNK_SIZE // 2


class TransferTests(E2ETestCase):

    async def assert_round_trip(self, size: int, parent_id: int, **upload_kwargs):
        source = self.create_local_file(size)

        node = await self.upload(source, parent_id=parent_id, **upload_kwargs)
        self.assertEqual(node.name, source.name)
        self.assertEqual(node.size, size)

        target_dir = self.local_dir / 'download'
        target_dir.mkdir()
        await self.dracoon.download(target_path=str(target_dir), source_node_id=node.id)

        self.assertEqual((target_dir / node.name).read_bytes(), source.read_bytes())
        return node

    async def test_small_file(self):
        folder = await self.create_folder()
        await self.assert_round_trip(1024, parent_id=folder.id)

    async def test_empty_file(self):
        folder = await self.create_folder()
        await self.assert_round_trip(0, parent_id=folder.id)

    async def test_multi_chunk_file(self):
        folder = await self.create_folder()
        await self.assert_round_trip(MULTI_CHUNK_SIZE, parent_id=folder.id, chunksize=MIN_CHUNK_SIZE)

    async def test_upload_to_path_and_download_from_path(self):
        folder = await self.create_folder()
        source = self.create_local_file(1024)

        folder_path = f'{folder.parentPath}{folder.name}/'
        target_dir = self.local_dir / 'download'
        target_dir.mkdir()

        await self.dracoon.upload(file_path=str(source), target_path=folder_path)
        await self.dracoon.download(target_path=str(target_dir), file_path=f'{folder_path}{source.name}')

        self.assertEqual((target_dir / source.name).read_bytes(), source.read_bytes())

    async def test_conflict_autorename(self):
        folder = await self.create_folder()
        source = self.create_local_file(1024)

        first = await self.upload(source, parent_id=folder.id)
        second = await self.upload(source, parent_id=folder.id, resolution_strategy='autorename')

        self.assertNotEqual(first.id, second.id)
        self.assertNotEqual(first.name, second.name)


class EncryptedTransferTests(E2ECryptoTestCase, TransferTests):
    """ same transfers in an encrypted room """

    async def create_folder(self, parent_id: int = None, name: str = None):
        return await super().create_folder(parent_id=parent_id or self.crypto_room_id, name=name)

    async def assert_round_trip(self, size: int, parent_id: int, **upload_kwargs):
        node = await super().assert_round_trip(size, parent_id, **upload_kwargs)
        self.assertTrue(node.isEncrypted)
        return node
