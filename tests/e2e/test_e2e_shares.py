from dracoon.errors import HTTPNotFoundError

from tests.e2e.harness import E2ETestCase


class DownloadShareTests(E2ETestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.folder = await self.create_folder()
        self.file = await self.upload(self.create_local_file(1024), parent_id=self.folder.id)

    async def test_create_get_update_delete(self):
        share = await self.create_share(node_id=self.file.id, notes='e2e')
        self.assertEqual(share.nodeId, self.file.id)

        fetched = await self.dracoon.shares.get_share(share_id=share.id)
        self.assertEqual(fetched.name, share.name)
        self.assertEqual(fetched.notes, 'e2e')

        updated = await self.dracoon.shares.update_share(share_id=share.id, share_update=self.dracoon.shares.make_share_update(max_downloads=5, notes='updated'))
        self.assertEqual(updated.maxDownloads, 5)
        self.assertEqual(updated.notes, 'updated')

        await self.dracoon.shares.delete_share(share_id=share.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.shares.get_share(share_id=share.id)

    async def test_list_filtered_by_node(self):
        share = await self.create_share(node_id=self.file.id)

        shares = await self.dracoon.shares.get_shares(filter=f'nodeId:eq:{self.file.id}')

        self.assertEqual([item.id for item in shares.items], [share.id])

    async def test_bulk_update_and_delete(self):
        shares = [await self.create_share(node_id=self.file.id) for _ in range(2)]
        share_ids = [share.id for share in shares]

        await self.dracoon.shares.update_shares(shares_update=self.dracoon.shares.make_shares_update(shares_list=share_ids, max_downloads=3))
        for share_id in share_ids:
            self.assertEqual((await self.dracoon.shares.get_share(share_id=share_id)).maxDownloads, 3)

        await self.dracoon.shares.delete_shares(share_list=share_ids)
        self.assertEqual((await self.dracoon.shares.get_shares(filter=f'nodeId:eq:{self.file.id}')).items, [])

    async def test_password_protected(self):
        share = await self.create_share(node_id=self.file.id, password='VerySecret123!')

        self.assertTrue(share.isProtected)


class FileRequestTests(E2ETestCase):

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.folder = await self.create_folder()

    async def test_create_get_update_delete(self):
        file_request = await self.create_file_request(target_id=self.folder.id, max_slots=2)
        self.assertEqual(file_request.targetId, self.folder.id)

        fetched = await self.dracoon.shares.get_file_request(file_request_id=file_request.id)
        self.assertEqual(fetched.name, file_request.name)
        self.assertEqual(fetched.maxSlots, 2)

        update = self.dracoon.shares.make_file_request_update(notes='updated', reset_max_slots=True)
        updated = await self.dracoon.shares.update_file_request(file_request_id=file_request.id, file_request_update=update)
        self.assertEqual(updated.notes, 'updated')
        self.assertIsNone(updated.maxSlots)

        await self.dracoon.shares.delete_file_request(file_request_id=file_request.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.shares.get_file_request(file_request_id=file_request.id)

    async def test_list_filtered_by_target(self):
        file_request = await self.create_file_request(target_id=self.folder.id)

        file_requests = await self.dracoon.shares.get_file_requests(filter=f'targetId:eq:{self.folder.id}')

        self.assertEqual([item.id for item in file_requests.items], [file_request.id])

    async def test_bulk_update_and_delete(self):
        file_requests = [await self.create_file_request(target_id=self.folder.id) for _ in range(2)]
        file_request_ids = [file_request.id for file_request in file_requests]

        update = self.dracoon.shares.make_file_requests_update(file_requests_list=file_request_ids, max_slots=3)
        await self.dracoon.shares.update_file_requests(file_requests_update=update)
        for file_request_id in file_request_ids:
            self.assertEqual((await self.dracoon.shares.get_file_request(file_request_id=file_request_id)).maxSlots, 3)

        await self.dracoon.shares.delete_file_requests(file_request_list=file_request_ids)
        self.assertEqual((await self.dracoon.shares.get_file_requests(filter=f'targetId:eq:{self.folder.id}')).items, [])
