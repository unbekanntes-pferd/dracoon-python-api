"""
E2E harness: isolated, self-cleaning tests against a real DRACOON instance.

Isolation
 - every test connects on its own and works in its own nodes / users / groups with unique names
   (e2e-<test>-<uuid>) - tests share no state and can run in parallel (pytest -n auto)
 - files and folders are created in a folder per test inside E2E_ROOM_ID, rooms as sub rooms of E2E_ROOM_ID

Cleanup
 - everything created via the helpers is deleted after the test (also on failure), in reverse order
 - deleted nodes end up in the recycle bin of E2E_ROOM_ID - use a room with a short retention period

Configuration (environment or .env, see .env.example) - tests are skipped if it is missing
"""
import os
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Optional, Union

import dotenv

from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.errors import HTTPNotFoundError
from dracoon.groups.responses import Group
from dracoon.nodes.models import Node
from dracoon.nodes.responses import S3FileUploadStatus
from dracoon.shares.responses import DownloadShare, UploadShare
from dracoon.user.responses import UserData

dotenv.load_dotenv()

REQUIRED = ('E2E_BASE_URL', 'E2E_USER_NAME', 'E2E_PASSWORD', 'E2E_ROOM_ID')


def env(name: str, default: str = None) -> Optional[str]:
    return os.environ.get(name) or default


def missing_config() -> list:
    return [name for name in REQUIRED if not env(name)]


class E2ETestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        missing = missing_config()
        if missing:
            raise unittest.SkipTest(f"E2E configuration missing: {', '.join(missing)}")

    async def asyncSetUp(self) -> None:
        self.room_id = int(env('E2E_ROOM_ID'))
        self.dracoon = DRACOON(base_url=env('E2E_BASE_URL'), client_id=env('CLIENT_ID', 'dracoon_legacy_scripting'),
                               client_secret=env('CLIENT_SECRET', ''), raise_on_err=True)
        await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=env('E2E_USER_NAME'), password=env('E2E_PASSWORD'))
        # cleanups run in reverse order - logout last
        self.addAsyncCleanup(self.dracoon.logout)

        local_dir = tempfile.TemporaryDirectory(prefix='dracoon-e2e-')
        self.addCleanup(local_dir.cleanup)
        self.local_dir = Path(local_dir.name)

    def unique_name(self, suffix: str = '') -> str:
        name = f"e2e-{self._testMethodName.removeprefix('test_')}-{uuid.uuid4().hex[:8]}"
        return f"{name}-{suffix}" if suffix else name

    def defer(self, delete_fn, *args, **kwargs) -> None:
        """ delete a created object after the test - objects already deleted by the test are ignored """
        async def cleanup():
            try:
                await delete_fn(*args, raise_on_err=True, **kwargs)
            except HTTPNotFoundError:
                pass
        self.addAsyncCleanup(cleanup)

    # nodes

    async def create_folder(self, parent_id: int = None, name: str = None) -> Node:
        """ folder in the test room (default) - deleted after the test """
        folder = self.dracoon.nodes.make_folder(name=name or self.unique_name(), parent_id=parent_id or self.room_id)
        node = await self.dracoon.nodes.create_folder(folder=folder)
        self.defer(self.dracoon.nodes.delete_node, node_id=node.id)
        return node

    async def create_room(self, **kwargs) -> Node:
        """ sub room of the test room - deleted after the test """
        kwargs.setdefault('inherit_perms', True)
        room = self.dracoon.nodes.make_room(name=self.unique_name(), parent_id=self.room_id, **kwargs)
        node = await self.dracoon.nodes.create_room(room=room)
        self.defer(self.dracoon.nodes.delete_node, node_id=node.id)
        return node

    # local files

    def create_local_file(self, size: int, name: str = None) -> Path:
        path = self.local_dir / (name or self.unique_name('upload.bin'))
        path.write_bytes(os.urandom(size))
        return path

    async def upload(self, path: Path, parent_id: int, **kwargs) -> Node:
        """ upload into a test folder (cleaned up with the folder) - returns the file node """
        result: Union[Node, S3FileUploadStatus] = await self.dracoon.upload(file_path=str(path), target_parent_id=parent_id, **kwargs)
        return result.node if isinstance(result, S3FileUploadStatus) else result

    # users, groups, shares

    async def create_user(self) -> UserData:
        """ local user (no notification) - deleted after the test """
        name = self.unique_name()
        email = f"{name}@{env('E2E_EMAIL_DOMAIN', 'example.com')}"
        payload = self.dracoon.users.make_local_user(first_name='E2E', last_name=name, email=email, login=email, notify=False)
        user = await self.dracoon.users.create_user(user=payload)
        self.defer(self.dracoon.users.delete_user, user_id=user.id)
        return user

    async def create_group(self) -> Group:
        """ group - deleted after the test """
        group = await self.dracoon.groups.create_group(group=self.dracoon.groups.make_group(name=self.unique_name()))
        self.defer(self.dracoon.groups.delete_group, group_id=group.id)
        return group

    async def create_share(self, node_id: int, **kwargs) -> DownloadShare:
        """ download share - deleted after the test (also removed with its node) """
        share = await self.dracoon.shares.create_share(share=self.dracoon.shares.make_share(node_id=node_id, name=self.unique_name(), **kwargs))
        self.defer(self.dracoon.shares.delete_share, share_id=share.id)
        return share

    async def create_file_request(self, target_id: int, **kwargs) -> UploadShare:
        """ file request (upload share) - deleted after the test (also removed with its node) """
        payload = self.dracoon.shares.make_file_request(target_id=target_id, name=self.unique_name(), **kwargs)
        file_request = await self.dracoon.shares.create_file_request(file_request=payload)
        self.defer(self.dracoon.shares.delete_file_request, file_request_id=file_request.id)
        return file_request


class E2ECryptoTestCase(E2ETestCase):
    """ encrypted room tests: E2E_CRYPTO_ROOM_ID (encrypted room) and E2E_CRYPTO_SECRET (existing user keypair) """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if not env('E2E_CRYPTO_ROOM_ID') or not env('E2E_CRYPTO_SECRET'):
            raise unittest.SkipTest('E2E crypto configuration missing: E2E_CRYPTO_ROOM_ID, E2E_CRYPTO_SECRET')

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        self.crypto_room_id = int(env('E2E_CRYPTO_ROOM_ID'))
        # the keypair is shared user state - it is only read, never created or deleted
        await self.dracoon.get_keypair(secret=env('E2E_CRYPTO_SECRET'))
