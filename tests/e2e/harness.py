"""
E2E harness: isolated, self-cleaning tests against a real DRACOON instance.

Test run
 - a top level room per run (e2e-run-<id>), created on first use - all nodes are created inside
 - encrypted tests: the e2e user gets a new keypair with a random secret and an encrypted top level room
   (e2e-run-<id>-crypto) - use a dedicated test user, its keypair is replaced
 - the rooms are deleted at the end of the run, also if tests failed (conftest.py)

Isolation
 - every test connects on its own and works in its own folders / rooms / users / groups with unique names
   (e2e-<test>-<uuid>) - tests share no state

Cleanup
 - everything created via the helpers is deleted after the test (also on failure), in reverse order

Configuration (environment or .env, see .env.example) - tests are skipped if it is missing
"""
import asyncio
import os
import secrets
import tempfile
import unittest
import uuid
from pathlib import Path
from typing import Callable, List, Optional, Union

import dotenv

from dracoon import DRACOON, OAuth2ConnectionType
from dracoon.crypto.models import UserKeyPairVersion
from dracoon.errors import HTTPNotFoundError
from dracoon.groups.responses import Group
from dracoon.nodes.models import Node
from dracoon.nodes.responses import S3FileUploadStatus
from dracoon.shares.responses import DownloadShare, UploadShare
from dracoon.user.responses import UserData

dotenv.load_dotenv()

REQUIRED = ('E2E_BASE_URL', 'E2E_USER_NAME', 'E2E_PASSWORD')
RUN_ID = uuid.uuid4().hex[:8]


def env(name: str, default: str = None) -> Optional[str]:
    return os.environ.get(name) or default


def missing_config() -> list:
    return [name for name in REQUIRED if not env(name)]


async def connect() -> DRACOON:
    dracoon = DRACOON(base_url=env('E2E_BASE_URL'), client_id=env('CLIENT_ID', 'dracoon_legacy_scripting'),
                      client_secret=env('CLIENT_SECRET', ''), raise_on_err=True)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=env('E2E_USER_NAME'), password=env('E2E_PASSWORD'))
    return dracoon


class TestRun:
    """ per run resources - created once on first use (outside of a running event loop), removed by cleanup() """

    def __init__(self):
        self.rooms: List[Node] = []
        self.resources = {}

    def get(self, name: str, factory: Callable):
        """ create a resource once - a failed setup fails every test that needs it """
        if name not in self.resources:
            try:
                self.resources[name] = asyncio.run(factory())
            except Exception as error:
                self.resources[name] = error
        resource = self.resources[name]
        if isinstance(resource, Exception):
            raise RuntimeError(f'E2E test run setup failed ({name}): {resource!r}') from resource
        return resource

    def room_id(self) -> int:
        return self.get('room', self._create_room)

    def crypto(self) -> tuple:
        """ (encrypted room id, keypair secret) """
        return self.get('crypto', self._create_crypto_room)

    async def _create_room(self, encrypted: bool = False) -> int:
        dracoon = await connect()
        try:
            name = f'e2e-run-{RUN_ID}-crypto' if encrypted else f'e2e-run-{RUN_ID}'
            room = dracoon.nodes.make_room(name=name, inherit_perms=False, admin_ids=[dracoon.user_info.id])
            node = await dracoon.nodes.create_room(room=room)
            self.rooms.append(node)
            if encrypted:
                await dracoon.nodes.encrypt_room(room_id=node.id, encrypt_room=dracoon.nodes.make_encrypt_room(is_encrypted=True))
            return node.id
        finally:
            await dracoon.logout()

    async def _create_crypto_room(self) -> tuple:
        # the room admin needs a keypair to encrypt the room
        secret = await self._reset_keypair()
        return await self._create_room(encrypted=True), secret

    @staticmethod
    async def _reset_keypair() -> str:
        """ replace the e2e user's keypair(s) with a new one protected by a random secret """
        secret = secrets.token_urlsafe(24)
        dracoon = await connect()
        try:
            for version in UserKeyPairVersion:
                try:
                    await dracoon.user.get_user_keypair(version=version)
                except HTTPNotFoundError:
                    continue
                await dracoon.user.delete_user_keypair(version=version)
            await dracoon.user.set_user_keypair(secret=secret)
        finally:
            await dracoon.logout()
        return secret

    async def cleanup(self) -> List[str]:
        """ delete the run rooms (room deletion is permanent - no recycle bin) - returns errors """
        errors = []
        if not self.rooms:
            return errors
        dracoon = await connect()
        try:
            for room in self.rooms:
                try:
                    await dracoon.nodes.delete_node(node_id=room.id)
                except Exception as error:
                    errors.append(f'{room.name} ({room.id}): {error!r}')
        finally:
            await dracoon.logout()
        self.rooms.clear()
        return errors


test_run = TestRun()


class E2ETestCase(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        missing = missing_config()
        if missing:
            raise unittest.SkipTest(f"E2E configuration missing: {', '.join(missing)}")
        cls.room_id = test_run.room_id()

    async def asyncSetUp(self) -> None:
        self.dracoon = await connect()
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
        """ folder in the run room (default) - deleted after the test """
        folder = self.dracoon.nodes.make_folder(name=name or self.unique_name(), parent_id=parent_id or self.room_id)
        node = await self.dracoon.nodes.create_folder(folder=folder)
        self.defer(self.dracoon.nodes.delete_node, node_id=node.id)
        return node

    async def create_room(self, **kwargs) -> Node:
        """ sub room of the run room - deleted after the test """
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
        # without notification (no invitation mail) an initial password is required
        payload.authData = self.dracoon.users.make_auth_data(method='basic', password=f'{secrets.token_urlsafe(24)}aA1!', change_password=True)
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
    """ encrypted room tests: encrypted run room, keypair with a random secret per run """

    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        cls.crypto_room_id, cls.crypto_secret = test_run.crypto()

    async def asyncSetUp(self) -> None:
        await super().asyncSetUp()
        # the keypair is shared user state - created once per run, only read in tests
        await self.dracoon.get_keypair(secret=self.crypto_secret)
