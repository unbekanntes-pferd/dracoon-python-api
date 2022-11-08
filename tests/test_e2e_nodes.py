import os
import asyncio
import random
import unittest
import dotenv
import logging
from pathlib import Path
from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.crypto.models import FileKey
from dracoon.errors import HTTPNotFoundError
from dracoon.nodes import DRACOONNodes
from dracoon.nodes.models import Node, NodeType
from dracoon.nodes.responses import (CommentList, DeletedNode, DeletedNodeSummaryList, DeletedNodeVersionsList, 
                                     DownloadTokenGenerateResponse, NodeList, NodeParentList)

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')
base_url_server = os.environ.get('E2E_SERVER_BASE_URL')

class DRACOONNodesTestsHelper():
    def __init__(self):
        self.cwd = Path.cwd()
        
    def generate_tiny_file(self):
        
        random_int = random.randrange(1000, 10000)
        file_path = Path.joinpath(self.cwd, f'test_file_{random_int}')
        
        with open(file_path, 'wb') as out_file:
            out_file.write(os.urandom(1024))
            
        return file_path

class TestAsyncDRACOONNodes(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def tearDownClass(cls) -> None:
        
        for file in os.listdir(Path.cwd()):
            if file.startswith('test_file_') or file.startswith('test_small_'):
                file_path = Path.joinpath(Path.cwd(), file)
                os.remove(file_path)
    
    async def asyncSetUp(self) -> None:
        
        asyncio.get_running_loop().set_debug(False)
        
        logging.disable(level=logging.CRITICAL)
        
        self.dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret, raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
        
        try:
            await self.dracoon.user.get_user_keypair(raise_on_err=True) 
            await self.dracoon.user.delete_user_keypair()
        except HTTPNotFoundError:
            pass
        
        await self.dracoon.user.set_user_keypair('VerySecret123!')
        await self.dracoon.get_keypair('VerySecret123!')
        
        logging.disable(level=logging.DEBUG)
        
        self.assertIsInstance(self.dracoon.nodes, DRACOONNodes)
        self.assertIsInstance(self.dracoon, DRACOON)
        self.assertIsNotNone(self.dracoon.connection)
        self.test_helper = DRACOONNodesTestsHelper()
        

    async def asyncTearDown(self) -> None:
        await self.dracoon.logout()
        
    async def test_get_nodes(self):
        nodes = await self.dracoon.nodes.get_nodes()
        self.assertIsInstance(nodes, NodeList)
 
    async def test_delete_nodes(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_DELETE_NODES')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        sub_room_1 = self.dracoon.nodes.make_room(name='SUB_1', inherit_perms=True, parent_id=target_node.id)
        sub_room_2 = self.dracoon.nodes.make_room(name='SUB_2', inherit_perms=True, parent_id=target_node.id)
        
        sub_1 = await self.dracoon.nodes.create_room(room=sub_room_1)
        sub_2 = await self.dracoon.nodes.create_room(room=sub_room_2)
        
 
        delete_nodes = await self.dracoon.nodes.delete_nodes(node_list=[sub_1.id, sub_2.id])
        self.assertEqual(delete_nodes, None)
        
        nodes = await self.dracoon.nodes.get_nodes(parent_id=target_node.id)
        self.assertEqual(len(nodes.items), 0)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
    async def test_get_node(self):
           
        room = self.dracoon.nodes.make_room(name='TEST_GET_NODE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        node_info = await self.dracoon.nodes.get_node(node_id=target_node.id)
        
        self.assertEqual(target_node, node_info)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
    async def delete_node(self):
        room = self.dracoon.nodes.make_room(name='TEST_DELETE_NODE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        del_node = await self.dracoon.nodes.delete_node(node_id=target_node.id)
        self.assertIsNone(del_node)
    
    async def test_get_add_node_comments(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_COMMENT_GET')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        comment = self.dracoon.nodes.make_comment(text="TEST COMMENT")
        await self.dracoon.nodes.add_node_comment(node_id=target_node.id, comment=comment)
        
        comments = await self.dracoon.nodes.get_node_comments(node_id=target_node.id)
        self.assertIsInstance(comments, CommentList)
        self.assertGreater(len(comments.items), 0)
        self.assertEqual(comments.items[0].text, "TEST COMMENT")
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
    
    async def test_copy_nodes(self):
        room = self.dracoon.nodes.make_room(name='TEST_COPY_NODES')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        room = self.dracoon.nodes.make_room(name='TEST_COPY_NODES_2')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        node_item = self.dracoon.nodes.make_node_item(node_id=folder.id)
        transfer = self.dracoon.nodes.make_node_transfer(items=[node_item])
        
        copy_folder = await self.dracoon.nodes.copy_nodes(target_id=target_node.id, copy_node=transfer)
        
        self.assertIsInstance(copy_folder, Node)
        
        node_info = await self.dracoon.nodes.get_nodes(parent_id=target_node.id)
        self.assertGreater(len(node_info.items), 0)
        self.assertEqual(node_info.items[0].name, folder.name)
        
        node_info = await self.dracoon.nodes.get_nodes(parent_id=source_node.id)
        self.assertGreater(len(node_info.items), 0)
        self.assertEqual(node_info.items[0].name, folder.name)
        
        await self.dracoon.nodes.delete_nodes(node_list=[target_node.id, source_node.id])

    async def test_move_nodes(self):
        room = self.dracoon.nodes.make_room(name='TEST_MOVE_NODES')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        room = self.dracoon.nodes.make_room(name='TEST_MOVE_NODES_2')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        node_item = self.dracoon.nodes.make_node_item(node_id=folder.id)
        transfer = self.dracoon.nodes.make_node_transfer(items=[node_item])
        
        copy_folder = await self.dracoon.nodes.move_nodes(target_id=target_node.id, move_node=transfer)
        
        self.assertIsInstance(copy_folder, Node)
        
        node_info = await self.dracoon.nodes.get_nodes(parent_id=target_node.id)
        self.assertGreater(len(node_info.items), 0)
        self.assertEqual(node_info.items[0].name, folder.name)

        node_info = await self.dracoon.nodes.get_nodes(parent_id=source_node.id)
        self.assertEqual(len(node_info.items), 0)
        
        await self.dracoon.nodes.delete_nodes(node_list=[target_node.id, source_node.id])

    async def get_deleted_nodes(self):
        room = self.dracoon.nodes.make_room(name='TEST_DELETED_NODES')
        source_node = await self.dracoon.nodes.create_room(room=room)
          
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        await self.dracoon.nodes.delete_node(node_id=folder.id)
        
        deleted_nodes = await self.dracoon.nodes.get_deleted_nodes(parent_id=source_node.id)
        
        self.assertIsInstance(deleted_nodes, DeletedNodeSummaryList)
        self.assertEqual(len(deleted_nodes.items), 1)
        
        deleted_node = deleted_nodes.items[0]
        self.assertEqual(deleted_node.name, folder.name)
        self.assertEqual(deleted_node.parentId, folder.parentId)
        self.assertEqual(deleted_node.lastDeletedNodeId, folder.id)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
        
    async def test_empty_node_recyclebin(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_EMPTY_BIN')
        source_node = await self.dracoon.nodes.create_room(room=room)
          
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        await self.dracoon.nodes.delete_node(node_id=folder.id)
        
        empty_bin = await self.dracoon.nodes.empty_node_recyclebin(parent_id=source_node.id) 
        self.assertIsNone(empty_bin)
        
        deleted_nodes = await self.dracoon.nodes.get_deleted_nodes(parent_id=source_node.id)
        self.assertEqual(len(deleted_nodes.items), 0)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)

    async def test_get_node_versions(self):
        room = self.dracoon.nodes.make_room(name='TEST_NODE_VERSIONS')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        file_path = self.test_helper.generate_tiny_file()
        
        file_upload = await self.dracoon.upload(file_path=file_path, target_parent_id=target_node.id)
        await self.dracoon.upload(file_path=file_path, target_parent_id=target_node.id, resolution_strategy='overwrite')
        await self.dracoon.upload(file_path=file_path, target_parent_id=target_node.id, resolution_strategy='overwrite')
        
        node_versions = await self.dracoon.nodes.get_node_versions(parent_id=target_node.id, name=file_upload.node.name, type='file')
        
        self.assertIsInstance(node_versions, DeletedNodeVersionsList)
        self.assertEqual(len(node_versions.items), 2)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
        
    async def test_add_favorite(self):
        room = self.dracoon.nodes.make_room(name='TEST_FAVORITES_ADD')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        favorite = await self.dracoon.nodes.add_favorite(node_id=target_node.id)      
        self.assertEqual(favorite.isFavorite, True)
        self.assertEqual(favorite.id, target_node.id)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
    
    async def test_delete_favorite(self):
        room = self.dracoon.nodes.make_room(name='TEST_FAVORITES_ADD')
        target_node = await self.dracoon.nodes.create_room(room=room)
        favorite = await self.dracoon.nodes.add_favorite(node_id=target_node.id)
        self.assertEqual(favorite.isFavorite, True)
        unfavorite = await self.dracoon.nodes.delete_favorite(node_id=target_node.id)
        self.assertIsNone(unfavorite)
        node_info = await self.dracoon.nodes.get_node(node_id=target_node.id)
        
        if node_info.isFavorite:
            self.assertFalse(node_info.isFavorite)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
            
    async def test_get_parents(self):
        room = self.dracoon.nodes.make_room(name='TEST_DELETE_NODES')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        sub_room_1 = self.dracoon.nodes.make_room(name='SUB_1', inherit_perms=True, parent_id=target_node.id)
 
        sub_1 = await self.dracoon.nodes.create_room(room=sub_room_1)
        
        parents = await self.dracoon.nodes.get_parents(node_id=sub_1.id)
        self.assertIsInstance(parents, NodeParentList)
        self.assertGreater(len(parents.items), 0)
        parent = parents.items[0]
        self.assertEqual(parent.name, target_node.name)
        self.assertEqual(parent.id, target_node.id)
        self.assertEqual(parent.type, target_node.type)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)
         
    async def test_empty_recyclebin(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_EMPTY_BIN_2')
        source_node = await self.dracoon.nodes.create_room(room=room)
          
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder_payload2 = self.dracoon.nodes.make_folder(name='test2', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        folder2 = await self.dracoon.nodes.create_folder(folder=folder_payload2)
        
        await self.dracoon.nodes.delete_nodes(node_list=[folder.id, folder2.id])
        
        empty_bin = await self.dracoon.nodes.empty_recyclebin(node_list=[folder.id, folder2.id])
        self.assertIsNone(empty_bin)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
    
    async def test_get_deleted_node(self):
        room = self.dracoon.nodes.make_room(name='TEST_GET_DELETED_NODE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=target_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        await self.dracoon.nodes.delete_node(node_id=folder.id)
        
        deleted_node = await self.dracoon.nodes.get_deleted_node(node_id=folder.id)
        self.assertIsInstance(deleted_node, DeletedNode)
        self.assertEqual(deleted_node.id, folder.id)
        self.assertEqual(deleted_node.name, folder.name)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)

    async def test_restore_node(self):
        room = self.dracoon.nodes.make_room(name='TEST_RESTORE_NODE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=target_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        await self.dracoon.nodes.delete_node(node_id=folder.id)
        
        node_restore = self.dracoon.nodes.make_node_restore(deleted_node_list=[folder.id])
        
        restored_node = await self.dracoon.nodes.restore_nodes(restore=node_restore)
        self.assertIsNone(restored_node)
        
        nodes = await self.dracoon.nodes.get_nodes(parent_id=target_node.id)
        self.assertGreater(len(nodes.items), 0)
        child_node = nodes.items[0]
        self.assertEqual(child_node.id, folder.id)
        self.assertEqual(child_node.name, folder.name)
        self.assertEqual(child_node.parentId, folder.parentId)
        self.assertEqual(child_node.parentPath, folder.parentPath)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)

    async def test_update_file(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_UPDATE_FILE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        file_path = self.test_helper.generate_tiny_file()
        
        file_upload = await self.dracoon.upload(file_path=file_path, target_parent_id=target_node.id)
        
        payload = self.dracoon.nodes.make_file_update(name='renamed.tiny.file')
        
        update_file = await self.dracoon.nodes.update_file(file_id=file_upload.node.id, file_update=payload)
        self.assertNotEqual(update_file.name, file_upload.node.name)
        self.assertEqual(update_file.id, file_upload.node.id)
        self.assertEqual(update_file.name, 'renamed.tiny.file')

        await self.dracoon.nodes.delete_node(node_id=target_node.id)

    async def test_update_files(self):
        
        room = self.dracoon.nodes.make_room(name='TEST_UPDATE_FILES')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        file_path_1 = self.test_helper.generate_tiny_file()
        file_path_2 = self.test_helper.generate_tiny_file()
        file_upload_1 = await self.dracoon.upload(file_path=file_path_1, target_parent_id=target_node.id)
        file_upload_2 = await self.dracoon.upload(file_path=file_path_2, target_parent_id=target_node.id)
        
        update_files = self.dracoon.nodes.make_files_update(files=[file_upload_1.node.id, file_upload_2.node.id], classification=3)
        files_update = await self.dracoon.nodes.update_files(files_update=update_files)
        self.assertIsNone(files_update)
        
        nodes = await self.dracoon.nodes.get_nodes(parent_id=target_node.id)
        self.assertEqual(len(nodes.items), 2)
        self.assertEqual(nodes.items[0].classification, 3)
        self.assertEqual(nodes.items[1].classification, 3)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)

    async def test_get_download_url(self):
        room = self.dracoon.nodes.make_room(name='TEST_UPDATE_FILE')
        target_node = await self.dracoon.nodes.create_room(room=room)
        
        file_path = self.test_helper.generate_tiny_file()
        
        file_upload = await self.dracoon.upload(file_path=file_path, target_parent_id=target_node.id)
        
        download_url_res = await self.dracoon.nodes.get_download_url(node_id=file_upload.node.id)
        
        self.assertIsInstance(download_url_res, DownloadTokenGenerateResponse)
        
        await self.dracoon.nodes.delete_node(node_id=target_node.id)


    async def test_get_user_file_key(self):
        room = self.dracoon.nodes.make_room(name='TEST_ENCRYPT_ROOM')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        encrypt_room_payload = self.dracoon.nodes.make_encrypt_room(is_encrypted=True)
        await self.dracoon.nodes.encrypt_room(room_id=source_node.id, encrypt_room=encrypt_room_payload)

        file_path = self.test_helper.generate_tiny_file()
        
        file_upload = await self.dracoon.upload(file_path=file_path, target_parent_id=source_node.id)
        
        file_key = await self.dracoon.nodes.get_user_file_key(file_id=file_upload.node.id)
        self.assertIsInstance(file_key, FileKey)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
  
    async def test_get_file_versions(self):
        self.skipTest("Not implemented")

    async def test_create_folder(self):
        room = self.dracoon.nodes.make_room(name='TEST_CREATE_FOLDER')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        self.assertIsInstance(folder, Node)
        self.assertEqual(folder.type, NodeType.folder)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
    
    async def test_update_folder(self):
        room = self.dracoon.nodes.make_room(name='TEST_UPDATE_FOLDER')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        folder_payload = self.dracoon.nodes.make_folder(name='test', parent_id=source_node.id)
        folder = await self.dracoon.nodes.create_folder(folder=folder_payload)
        
        folder_update = self.dracoon.nodes.make_folder_update(name='test.renamed')
        update = await self.dracoon.nodes.update_folder(node_id=folder.id, folder_update=folder_update)
        self.assertIsInstance(update, Node)
        self.assertEqual(update.name, 'test.renamed')
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
        
    async def test_create_room(self):
        room = self.dracoon.nodes.make_room(name='TEST_CREATE_ROOM')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        self.assertIsInstance(source_node, Node)
        self.assertEqual(source_node.type, NodeType.room)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
    
    async def test_update_room(self):
        room = self.dracoon.nodes.make_room(name='TEST_UPDATE_ROOM')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        room_update = self.dracoon.nodes.make_room_update(name=f"{source_node.name}_RENAMED")
        update = await self.dracoon.nodes.update_room(node_id=source_node.id, room_update=room_update)
        self.assertIsInstance(update, Node)
        self.assertEqual(update.name, f"{source_node.name}_RENAMED")
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)
    
    async def test_encrypt_room(self):
        room = self.dracoon.nodes.make_room(name='TEST_ENCRYPT_ROOM')
        source_node = await self.dracoon.nodes.create_room(room=room)
        
        encrypt_room_payload = self.dracoon.nodes.make_encrypt_room(is_encrypted=True)
        encrypt_room = await self.dracoon.nodes.encrypt_room(room_id=source_node.id, encrypt_room=encrypt_room_payload)
        
        self.assertIsInstance(encrypt_room, Node)
        self.assertTrue(encrypt_room.isEncrypted)
        
        await self.dracoon.nodes.delete_node(node_id=source_node.id)

"""
    async def test_config_room(self):
        self.skipTest("Not implemented")
        
    async def test_get_room_groups(self):
        self.skipTest("Not implemented")
    
    async def test_update_room_groups(self):
        self.skipTest("Not implemented")
    
    async def test_delete_room_groups(self):
        self.skipTest("Not implemented")
    
    async def test_get_room_users(self):
        self.skipTest("Not implemented")
    
    async def test_update_room_users(self):
        self.skipTest("Not implemented")
    
    async def test_delete_room_users(self):
        self.skipTest("Not implemented")
    
    async def test_get_room_webhooks(self):
        self.skipTest("Not implemented")
    
    async def test_update_room_webhooks(self):
        self.skipTest("Not implemented")
    
    async def test_get_room_events(self):
        self.skipTest("Not implemented")
    
    async def test_get_pending_assignments(self):
        self.skipTest("Not implemented")
    
    async def test_process_pending_assignments(self):
        self.skipTest("Not implemented")
    
    async def test_search_nodes(self):
        self.skipTest("Not implemented")
        
    async def test_set_file_keys(self):
        self.skipTest("Not implemented")
    
    async def test_get_missing_file_keys(self):
        self.skipTest("Not implemented") """
    

if __name__ == '__main__':
    unittest.main()
