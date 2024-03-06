import unittest
import respx
import asyncio

import json
from datetime import datetime

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.nodes import DRACOONNodes
from dracoon.nodes.models import NodeType
from dracoon.crypto.models import FileKeyVersion

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
DEFAULT_STRING = 'string'
DEFAULT_DATE = '2020-01-01T00:00:00.000Z'
DEFAULT_PARSED_DATE = datetime.strptime(DEFAULT_DATE, '%Y-%m-%dT%H:%M:%S.%fZ')


class TestAsyncDRACOONNodes(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:

        with open('tests/responses/nodes/nodes_ok.json', 'r') as json_file:
            self.nodes_json = json.load(json_file)
        
        with open('tests/responses/nodes/node_ok.json', 'r') as json_file:
            self.node_json = json.load(json_file)
        
        with open('tests/responses/nodes/folder_ok.json', 'r') as json_file:
            self.folder_json = json.load(json_file)

        with open('tests/responses/nodes/missing_file_keys_ok.json', 'r') as json_file:
            self.missing_keys_json = json.load(json_file)

        with open('tests/responses/nodes/missing_file_keys_empty_ok.json', 'r') as json_file:
            self.missing_keys_empty_json = json.load(json_file)

        with open('tests/responses/nodes/nodes_search_no_result.json', 'r') as json_file:
            self.search_empty_json = json.load(json_file)
        
        with open('tests/responses/download/download_url_ok.json', 'r') as json_file:
            self.download_url_json = json.load(json_file)
        
        with open('tests/responses/download/file_key_ok.json', 'r') as json_file:
            self.file_key_json = json.load(json_file)
        
        with open('tests/responses/nodes/room_groups_ok.json', 'r') as json_file:
            self.room_groups_json = json.load(json_file)

        return super().setUp()

    def assert_node(self, node, is_folder: bool = False) -> None:
        assert node.id == 2
        assert node.referenceId == 2
        if is_folder:
            assert node.type == NodeType.folder
        else:
            assert node.type == NodeType.room
        assert node.name == DEFAULT_STRING
        assert node.parentPath == DEFAULT_STRING
        assert node.parentId == 1
        created_by = node.createdBy
        assert created_by.id == 3
        assert created_by.userName == DEFAULT_STRING
        assert created_by.firstName == DEFAULT_STRING
        assert created_by.lastName == DEFAULT_STRING
        assert created_by.email == DEFAULT_STRING
        assert created_by.avatarUuid == DEFAULT_STRING
        updated_by = node.updatedBy
        assert updated_by.id == 3
        assert updated_by.userName == DEFAULT_STRING
        assert updated_by.firstName == DEFAULT_STRING
        assert updated_by.lastName == DEFAULT_STRING
        assert updated_by.email == DEFAULT_STRING
        assert updated_by.avatarUuid == DEFAULT_STRING
        assert node.size == 123456
        assert node.classification == 4
        assert node.notes == DEFAULT_STRING
        node_permissions = node.permissions
        assert node_permissions.manage == True
        assert node_permissions.read == True
        assert node_permissions.create == True
        assert node_permissions.change == True
        assert node_permissions.delete == True
        assert node_permissions.manageDownloadShare == True
        assert node_permissions.manageUploadShare == True
        assert node_permissions.readRecycleBin == True
        assert node_permissions.restoreRecycleBin == True
        assert node_permissions.deleteRecycleBin == True
        assert node.inheritPermissions == True
        assert node.isEncrypted == False
        assert node.quota == 0
        assert node.isFavorite == True
        assert node.branchVersion == 123456
        assert node.authParentId == 1
        assert node.cntRooms == 1
        assert node.cntFolders == 2
        assert node.cntFiles == 3
        assert node.mediaToken == DEFAULT_STRING
        assert node.cntDownloadShares == 0
        assert node.cntUploadShares == 0
        assert node.cntComments == 0
        assert node.recycleBinRetentionPeriod == 9999

    @respx.mock
    async def asyncSetUp(self) -> None:

        # needed because keypair generation takes a second
        asyncio.get_running_loop().set_debug(False)

        self.client = DRACOONClient(
            base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET, raise_on_err=True)
        with open('tests/responses/auth/auth_ok.json', 'r') as json_file:
            login_json = json.load(json_file)
            login_mock = respx.post(
                f'{BASE_URL}/oauth/token').respond(200, json=login_json)
            await self.client.connect(username='test_user', password='test_password', connection_type=OAuth2ConnectionType.password_flow)

            assert login_mock.called
            assert self.client.connected

            self.nodes = DRACOONNodes(self.client)

            return await super().asyncSetUp()
        
    @respx.mock
    async def test_get_nodes(self):
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset=0&parent_id=0&room_manager=false').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes()
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)

    @respx.mock
    async def test_get_nodes_with_room_manager(self):
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset=0&parent_id=0&room_manager=true').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes(room_manager=True)
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)

    @respx.mock
    async def test_get_nodes_with_offset(self):
        offset = 100
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset={offset}&parent_id=0&room_manager=false').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes(offset=offset)
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_get_nodes_with_limit(self):
        limit = 1
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset=0&parent_id=0&room_manager=false&limit={limit}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes(limit=limit)
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)

    @respx.mock
    async def test_get_nodes_with_filter(self):
        filter = 'name:cn:test'
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset=0&parent_id=0&room_manager=false&filter={filter}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes(filter=filter)
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)

    @respx.mock
    async def test_get_nodes_with_sort(self):
        sort = 'name:asc'
        get_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes?offset=0&parent_id=0&room_manager=false&sort={sort}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.get_nodes(sort=sort)
        assert get_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)

    @respx.mock
    async def test_delete_nodes(self):
        delete_nodes_mock = respx.delete(
            f'{BASE_URL}/api/v4/nodes').respond(204)
        await self.nodes.delete_nodes([1])
        assert delete_nodes_mock.called

    @respx.mock
    async def test_get_node(self):
        node_id = 1
        get_node_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/{node_id}').respond(200, json=self.node_json)
        node = await self.nodes.get_node(node_id=node_id)
        assert get_node_mock.called
        self.assert_node(node)

    @respx.mock
    async def test_delete_node(self):
        node_id = 1
        delete_node_mock = respx.delete(
            f'{BASE_URL}/api/v4/nodes/{node_id}').respond(204)
        await self.nodes.delete_node(node_id=node_id)
        assert delete_node_mock.called

    @respx.mock
    async def test_copy_nodes(self):
        parent_id = 2
        node_item = self.nodes.make_node_item(node_id=1)
        node_transfer = self.nodes.make_node_transfer(items=[node_item])

        copy_nodes_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/{parent_id}/copy_to').respond(200, json=self.node_json)
        node = await self.nodes.copy_nodes(target_id=parent_id, copy_node=node_transfer)
        assert copy_nodes_mock.called
        self.assert_node(node)

    @respx.mock
    async def test_move_nodes(self):
        parent_id = 2
        node_item = self.nodes.make_node_item(node_id=1)
        node_transfer = self.nodes.make_node_transfer(items=[node_item])

        copy_nodes_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/{parent_id}/move_to').respond(200, json=self.node_json)
        node = await self.nodes.move_nodes(target_id=parent_id, move_node=node_transfer)
        assert copy_nodes_mock.called
        self.assert_node(node)
    
    @respx.mock
    async def test_add_favorite(self):
        node_id = 1
        add_favorite_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/{node_id}/favorite').respond(200, json=self.node_json)
        node = await self.nodes.add_favorite(node_id=node_id)
        assert add_favorite_mock.called
        self.assert_node(node)
    
    @respx.mock
    async def test_delete_favorite(self):
        node_id = 1
        delete_favorite_mock = respx.delete(
            f'{BASE_URL}/api/v4/nodes/{node_id}/favorite').respond(204)
        await self.nodes.delete_favorite(node_id=node_id)
        assert delete_favorite_mock.called

    @respx.mock
    async def test_restore_nodes(self):
        restore_node = self.nodes.make_node_restore(deleted_node_list=[1, 2])
        restore_nodes_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/deleted_nodes/actions/restore').respond(204)
        await self.nodes.restore_nodes(restore=restore_node)
        assert restore_nodes_mock.called
    
    @respx.mock
    async def test_get_download_url(self):
        node_id = 1
        get_download_url_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/files/{node_id}/downloads').respond(200, json=self.download_url_json)
        node = await self.nodes.get_download_url(node_id=node_id)
        assert get_download_url_mock.called
        assert node.downloadUrl == "https://test.dracoon.com/not/real/download_url"
    
    @respx.mock
    async def test_get_user_file_key(self):
        node_id = 1
        get_user_file_key_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/files/{node_id}/user_file_key').respond(200, json=self.file_key_json)
        file_key = await self.nodes.get_user_file_key(file_id=node_id)
        assert get_user_file_key_mock.called
        assert file_key.key == DEFAULT_STRING
        assert file_key.iv == DEFAULT_STRING
        assert file_key.tag == DEFAULT_STRING
        assert file_key.version == "RSA-4096/AES-256-GCM"
    
    @respx.mock
    async def test_set_file_keys(self):
        file_key_mock = {
            "key": DEFAULT_STRING,
            "iv": DEFAULT_STRING,
            "tag": DEFAULT_STRING,
            "version": "RSA-4096/AES-256-GCM"
        }

        file_key_item = self.nodes.make_set_file_key_item(file_id=1, user_id=2, file_key=file_key_mock)
        payload = self.nodes.make_set_file_keys(file_key_list=[file_key_item])

        set_file_keys_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/files/keys').respond(204)
        
        await self.nodes.set_file_keys(file_keys=payload)
        assert set_file_keys_mock.called
    
    @respx.mock
    async def test_create_folder(self):
        folder_payload = self.nodes.make_folder(name=DEFAULT_STRING, parent_id=1)
        create_folder_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/folders').respond(201, json=self.folder_json)
        folder = await self.nodes.create_folder(folder=folder_payload)
        assert create_folder_mock.called
        self.assert_node(folder, is_folder=True)
    
    @respx.mock
    async def test_update_folder(self):
        node_id = 1
        folder_payload = self.nodes.make_folder_update(name=DEFAULT_STRING)
        update_folder_mock = respx.put(
            f'{BASE_URL}/api/v4/nodes/folders/{node_id}').respond(200, json=self.folder_json)
        folder = await self.nodes.update_folder(node_id=node_id, folder_update=folder_payload)
        assert update_folder_mock.called
        self.assert_node(folder, is_folder=True)
    
    @respx.mock
    async def test_get_missing_file_keys(self):
        get_missing_file_keys_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/missingFileKeys').respond(200, json=self.missing_keys_json)
        missing_keys = await self.nodes.get_missing_file_keys()
        assert get_missing_file_keys_mock.called
        assert len(missing_keys.items) == 1
        assert len(missing_keys.users) == 1
        assert len(missing_keys.files) == 1
        item = missing_keys.items[0]
        assert item.fileId == 3
        assert item.userId == 2
        user = missing_keys.users[0]
        assert user.id == 2
        assert user.publicKeyContainer.version == "RSA-4096"
        assert user.publicKeyContainer.createdBy == 1
        file = missing_keys.files[0]
        assert file.id == 3
        assert file.fileKeyContainer.version == "RSA-4096/AES-256-GCM"
        assert file.fileKeyContainer.key == DEFAULT_STRING
        assert file.fileKeyContainer.iv == DEFAULT_STRING
        assert file.fileKeyContainer.tag == DEFAULT_STRING
    
    @respx.mock
    async def test_create_room(self):
        room_payload = self.nodes.make_room(name=DEFAULT_STRING)
        create_room_mock = respx.post(
            f'{BASE_URL}/api/v4/nodes/rooms').respond(201, json=self.node_json)
        room = await self.nodes.create_room(room=room_payload)
        assert create_room_mock.called
        self.assert_node(room)
    
    @respx.mock
    async def test_update_room(self):
        room_id = 1
        room_update = self.nodes.make_room_update(name=DEFAULT_STRING)
        update_room_mock = respx.put(
            f'{BASE_URL}/api/v4/nodes/rooms/{room_id}').respond(200, json=self.node_json)
        room = await self.nodes.update_room(node_id=room_id, room_update=room_update)
        assert update_room_mock.called
        self.assert_node(room)
    
    @respx.mock
    async def test_config_room(self):
        room_id = 1
        room_config = self.nodes.make_room_config(classification=4, notes=DEFAULT_STRING)
        config_room_mock = respx.put(
            f'{BASE_URL}/api/v4/nodes/rooms/{room_id}/config').respond(200, json=self.node_json)
        node = await self.nodes.config_room(node_id=room_id, config_update=room_config)
        assert config_room_mock.called
        self.assert_node(node)
    
    @respx.mock
    async def test_encrypt_room(self):
        room_id = 1
        encrypt_payload = self.nodes.make_encrypt_room(is_encrypted=True)
        encrypt_room_mock = respx.put(
            f'{BASE_URL}/api/v4/nodes/rooms/{room_id}/encrypt').respond(200, json=self.node_json)
        node = await self.nodes.encrypt_room(room_id=room_id, encrypt_room=encrypt_payload)
        assert encrypt_room_mock.called
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes(self):
        search = "*"
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id=0&depth_level=0').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_offset(self):
        search = "*"
        offset = 100
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset={offset}&search_string={search}&parent_id=0&depth_level=0').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, offset=offset)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_depth_level(self):
        search = "*"
        depth_level = 1
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id=0&depth_level={depth_level}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, depth_level=depth_level)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_limit(self):
        search = "*"
        limit = 1
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id=0&depth_level=0&limit={limit}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, limit=limit)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_sort(self):
        search = "*"
        sort = 'name:asc'
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id=0&depth_level=0&sort={sort}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, sort=sort)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_filter(self):
        search = "*"
        filter = 'name:cn:test'
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id=0&depth_level=0&filter={filter}').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, filter=filter)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    
    @respx.mock
    async def test_search_nodes_with_parent_id(self):
        search = "*"
        parent_id = 1
        search_nodes_mock = respx.get(
            f'{BASE_URL}/api/v4/nodes/search?offset=0&search_string={search}&parent_id={parent_id}&depth_level=0').respond(200, json=self.nodes_json)
        nodes = await self.nodes.search_nodes(search=search, parent_id=parent_id)
        assert search_nodes_mock.called
        assert len(nodes.items) == 1
        node = nodes.items[0]
        self.assert_node(node)
    



        




    