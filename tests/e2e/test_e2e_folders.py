from dracoon.errors import HTTPNotFoundError
from dracoon.nodes.models import NodeType

from tests.e2e.harness import E2ETestCase


class FolderTests(E2ETestCase):

    async def test_create_get_update_delete(self):
        parent = await self.create_folder()

        folder = await self.create_folder(parent_id=parent.id)
        self.assertEqual(folder.type, NodeType.folder)
        self.assertEqual(folder.parentId, parent.id)

        fetched = await self.dracoon.nodes.get_node(node_id=folder.id)
        self.assertEqual(fetched.name, folder.name)

        new_name = self.unique_name('renamed')
        updated = await self.dracoon.nodes.update_folder(node_id=folder.id, folder_update=self.dracoon.nodes.make_folder_update(name=new_name, notes='e2e'))
        self.assertEqual(updated.name, new_name)
        self.assertEqual(updated.notes, 'e2e')

        await self.dracoon.nodes.delete_node(node_id=folder.id)
        with self.assertRaises(HTTPNotFoundError):
            await self.dracoon.nodes.get_node(node_id=folder.id)

    async def test_list_children(self):
        parent = await self.create_folder()
        children = [await self.create_folder(parent_id=parent.id) for _ in range(3)]

        nodes = await self.dracoon.nodes.get_nodes(parent_id=parent.id)

        self.assertEqual({node.id for node in nodes.items}, {child.id for child in children})

    async def test_get_node_from_path(self):
        parent = await self.create_folder()
        folder = await self.create_folder(parent_id=parent.id)

        node = await self.dracoon.nodes.get_node_from_path(path=f'{folder.parentPath}{folder.name}/')

        self.assertEqual(node.id, folder.id)

    async def test_search(self):
        parent = await self.create_folder()
        folder = await self.create_folder(parent_id=parent.id)

        result = await self.dracoon.nodes.search_nodes(search=folder.name, parent_id=parent.id)

        self.assertEqual([node.id for node in result.items], [folder.id])

    async def test_copy_and_move(self):
        source = await self.create_folder()
        target = await self.create_folder()
        file = await self.upload(self.create_local_file(1024), parent_id=source.id)

        transfer = self.dracoon.nodes.make_node_transfer(items=[self.dracoon.nodes.make_node_item(node_id=file.id)])
        await self.dracoon.nodes.copy_nodes(target_id=target.id, copy_node=transfer)
        self.assertEqual([node.name for node in (await self.dracoon.nodes.get_nodes(parent_id=target.id)).items], [file.name])

        moved_into = await self.create_folder()
        await self.dracoon.nodes.move_nodes(target_id=moved_into.id, move_node=transfer)
        self.assertEqual((await self.dracoon.nodes.get_nodes(parent_id=source.id)).items, [])
        self.assertEqual([node.id for node in (await self.dracoon.nodes.get_nodes(parent_id=moved_into.id)).items], [file.id])

    async def test_delete_nodes(self):
        parent = await self.create_folder()
        children = [await self.create_folder(parent_id=parent.id) for _ in range(2)]

        await self.dracoon.nodes.delete_nodes(node_list=[child.id for child in children])

        self.assertEqual((await self.dracoon.nodes.get_nodes(parent_id=parent.id)).items, [])

    async def test_comments(self):
        folder = await self.create_folder()

        comment = await self.dracoon.nodes.add_node_comment(node_id=folder.id, comment=self.dracoon.nodes.make_comment('e2e comment'))
        comments = await self.dracoon.nodes.get_node_comments(node_id=folder.id)

        self.assertEqual([item.id for item in comments.items], [comment.id])
