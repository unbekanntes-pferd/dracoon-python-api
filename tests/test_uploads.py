import unittest
import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import respx

from dracoon.client import DRACOONClient
from dracoon.client.models import DRACOONConnection
from dracoon.nodes import DRACOONNodes
from dracoon.nodes.responses import CreateFileUploadResponse
from dracoon.crypto import create_plain_userkeypair, decrypt_file_key, decrypt_bytes
from dracoon.crypto.models import FileKey, UserKeyPairVersion
from dracoon.errors import UploadTimeoutError

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
API_URL = f'{BASE_URL}/api/v4'
UPLOAD_TOKEN = 'upload_token'
UPLOAD_ID = 'upload_id'
UPLOAD_URL = f'{API_URL}/uploads/{UPLOAD_TOKEN}'
S3_URL = 'https://s3.dracoon.team/bucket/part'
NODE_ID = 2
RECIPIENT_USER_ID = 5
FILE_SIZE = 1000
CHUNK_SIZE = 256


def file_content(size: int) -> bytes:
    """ deterministic test data """
    return (bytes(range(256)) * (size // 256 + 1))[:size]


def multipart_file(request: httpx.Request) -> bytes:
    """ extract the file part of a multipart/form-data request (proxy uploads) """
    boundary = request.headers['Content-Type'].split('boundary=')[1].encode()
    part = request.content.split(b'--' + boundary)[1]
    # part: headers, blank line, body, trailing CRLF
    return part.split(b'\r\n\r\n', 1)[1][:-2]


class CallbackRecorder:
    """ records transfer progress callbacks """
    def __init__(self):
        self.total = None
        self.transferred = 0

    def __call__(self, val: int, total: int = None):
        if total is not None:
            self.total = total
        self.transferred += val


class TestAsyncDRACOONUploads(unittest.IsolatedAsyncioTestCase):

    @classmethod
    def setUpClass(cls) -> None:
        cls.plain_keypair = create_plain_userkeypair(version=UserKeyPairVersion.RSA2048)
        cls.recipient_keypair = create_plain_userkeypair(version=UserKeyPairVersion.RSA4096)

    def setUp(self) -> None:

        with open('tests/responses/nodes/node_ok.json', 'r') as json_file:
            self.node_json = json.load(json_file)

        with open('tests/responses/upload/upload_status_ok.json', 'r') as json_file:
            self.upload_status_json = json.load(json_file)

        with open('tests/responses/upload/upload_status_pending_ok.json', 'r') as json_file:
            self.upload_status_pending_json = json.load(json_file)

        with open('tests/responses/nodes/missing_file_keys_empty_ok.json', 'r') as json_file:
            self.missing_keys_empty_json = json.load(json_file)

        self.dracoon = DRACOONClient(base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)
        self.dracoon.connection = DRACOONConnection(datetime.now(), 'access_token', 3600, 'refresh_token')
        self.dracoon.connected = True
        self.nodes = DRACOONNodes(self.dracoon)

        self.upload_channel = CreateFileUploadResponse(uploadUrl=UPLOAD_URL, uploadId=UPLOAD_ID, token=UPLOAD_TOKEN)

        self.tmp_dir = tempfile.TemporaryDirectory()
        self.data = file_content(FILE_SIZE)
        self.file_path = Path(self.tmp_dir.name).joinpath('test.bin')
        self.file_path.write_bytes(self.data)

        return super().setUp()

    async def asyncTearDown(self) -> None:
        await self.dracoon.disconnect()
        self.tmp_dir.cleanup()

    # mocks

    def mock_proxy_upload(self):
        upload_mock = respx.post(UPLOAD_URL).respond(201)
        complete_mock = respx.put(UPLOAD_URL).respond(201, json=self.node_json)
        return upload_mock, complete_mock

    def mock_s3_upload(self, status_responses: list = None):
        """ S3 presigned urls per requested part range, PUT returns ETag per part, polling returns given status responses """

        def s3_urls(request: httpx.Request) -> httpx.Response:
            payload = json.loads(request.content)
            urls = [{"url": f'{S3_URL}/{part}', "partNumber": part}
                    for part in range(payload["firstPartNumber"], payload["lastPartNumber"] + 1)]
            return httpx.Response(201, json={"urls": urls})

        def s3_put(request: httpx.Request) -> httpx.Response:
            part = request.url.path.split('/')[-1]
            return httpx.Response(200, headers={"ETag": f'"etag-{part}"'})

        if status_responses is None:
            status_responses = [self.upload_status_json]

        s3_urls_mock = respx.post(f'{API_URL}/nodes/files/uploads/{UPLOAD_ID}/s3_urls').mock(side_effect=s3_urls)
        s3_put_mock = respx.put(url__startswith=S3_URL).mock(side_effect=s3_put)
        complete_mock = respx.put(f'{API_URL}/nodes/files/uploads/{UPLOAD_ID}/s3').respond(202)
        status_mock = respx.get(f'{API_URL}/nodes/files/uploads/{UPLOAD_ID}').mock(
            side_effect=[httpx.Response(200, json=status) for status in status_responses])
        return s3_urls_mock, s3_put_mock, complete_mock, status_mock

    def mock_missing_keys_for_recipient(self, get_file_key):
        """ missing file key for a recipient user - file key is taken from the completed upload """

        def missing_keys(request: httpx.Request) -> httpx.Response:
            return httpx.Response(200, json={
                "range": {"offset": 0, "limit": 0, "total": 1},
                "items": [{"userId": RECIPIENT_USER_ID, "fileId": NODE_ID}],
                "users": [{"id": RECIPIENT_USER_ID, "publicKeyContainer": self.recipient_keypair.publicKeyContainer.model_dump()}],
                "files": [{"id": NODE_ID, "fileKeyContainer": get_file_key()}]
            })

        respx.get(f'{API_URL}/nodes/missingFileKeys').mock(side_effect=missing_keys)
        return respx.post(f'{API_URL}/nodes/files/keys').respond(204)

    # assertions

    def assert_decrypts_to_data(self, enc_data: bytes, file_key: dict):
        plain_file_key = decrypt_file_key(file_key=FileKey(**file_key), keypair=self.plain_keypair)
        assert decrypt_bytes(enc_data, plain_file_key) == self.data

    def assert_recipient_file_key(self, set_keys_mock, file_key: dict):
        """ recipient must receive the same plain file key, encrypted with their public key """
        payload = json.loads(set_keys_mock.calls.last.request.content)
        assert len(payload["items"]) == 1
        item = payload["items"][0]
        assert item["fileId"] == NODE_ID
        assert item["userId"] == RECIPIENT_USER_ID

        recipient_file_key = decrypt_file_key(file_key=FileKey(**item["fileKey"]), keypair=self.recipient_keypair)
        uploader_file_key = decrypt_file_key(file_key=FileKey(**file_key), keypair=self.plain_keypair)
        assert recipient_file_key.key == uploader_file_key.key
        assert recipient_file_key.iv == uploader_file_key.iv

    # proxy uploads

    @respx.mock
    async def test_upload_unencrypted(self):
        upload_mock, complete_mock = self.mock_proxy_upload()
        callback = CallbackRecorder()

        node = await self.nodes.upload_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, callback_fn=callback)

        assert upload_mock.call_count == 1
        assert upload_mock.calls.last.request.content == self.data
        assert json.loads(complete_mock.calls.last.request.content) == {"resolutionStrategy": "autorename", "keepShareLinks": False,
                                                                       "fileName": "test.bin"}
        assert node.id == NODE_ID
        assert callback.total == FILE_SIZE
        assert callback.transferred == FILE_SIZE

    @respx.mock
    async def test_upload_unencrypted_chunked(self):
        upload_mock, complete_mock = self.mock_proxy_upload()
        callback = CallbackRecorder()

        node = await self.nodes.upload_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, chunksize=CHUNK_SIZE,
                                                   file_name='renamed.bin', resolution_strategy='overwrite', callback_fn=callback)

        assert upload_mock.call_count == 4
        assert b''.join(multipart_file(call.request) for call in upload_mock.calls) == self.data
        assert json.loads(complete_mock.calls.last.request.content) == {"resolutionStrategy": "overwrite", "keepShareLinks": False,
                                                                       "fileName": "renamed.bin"}
        assert node.id == NODE_ID
        assert callback.transferred == FILE_SIZE

    @respx.mock
    async def test_upload_unencrypted_chunked_content_range(self):
        upload_mock, _ = self.mock_proxy_upload()

        await self.nodes.upload_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, chunksize=CHUNK_SIZE)

        content_ranges = [call.request.headers['Content-Range'] for call in upload_mock.calls]
        assert content_ranges == ['bytes 0-255/1000', 'bytes 256-511/1000', 'bytes 512-767/1000', 'bytes 768-999/1000']

    @respx.mock
    async def test_upload_chunked_does_not_leak_headers(self):
        upload_mock, _ = self.mock_proxy_upload()

        await self.nodes.upload_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, chunksize=CHUNK_SIZE)
        await self.nodes.upload_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel)

        assert 'Content-Range' not in self.dracoon.uploader.headers
        assert 'Content-Range' not in upload_mock.calls.last.request.headers

    @respx.mock
    async def test_upload_encrypted(self):
        upload_mock, complete_mock = self.mock_proxy_upload()
        missing_keys_mock = respx.get(f'{API_URL}/nodes/missingFileKeys').respond(200, json=self.missing_keys_empty_json)
        callback = CallbackRecorder()

        node = await self.nodes.upload_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                                 plain_keypair=self.plain_keypair, callback_fn=callback)

        assert upload_mock.call_count == 1
        payload = json.loads(complete_mock.calls.last.request.content)
        assert payload["resolutionStrategy"] == "autorename"
        assert payload["fileName"] == "test.bin"
        self.assert_decrypts_to_data(multipart_file(upload_mock.calls.last.request), payload["fileKey"])
        assert missing_keys_mock.calls.last.request.url.params['file_id'] == str(NODE_ID)
        assert node.id == NODE_ID
        assert callback.transferred == FILE_SIZE

    @respx.mock
    async def test_upload_encrypted_chunked(self):
        upload_mock, complete_mock = self.mock_proxy_upload()
        respx.get(f'{API_URL}/nodes/missingFileKeys').respond(200, json=self.missing_keys_empty_json)

        await self.nodes.upload_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                          plain_keypair=self.plain_keypair, chunksize=CHUNK_SIZE)

        assert upload_mock.call_count == 4
        enc_data = b''.join(multipart_file(call.request) for call in upload_mock.calls)
        self.assert_decrypts_to_data(enc_data, json.loads(complete_mock.calls.last.request.content)["fileKey"])

    @respx.mock
    async def test_upload_encrypted_distributes_all_missing_file_key_pages(self):
        _, complete_mock = self.mock_proxy_upload()
        get_file_key = lambda: json.loads(complete_mock.calls.last.request.content)["fileKey"]
        user_ids = list(range(100, 160))
        public_key = self.recipient_keypair.publicKeyContainer.model_dump()

        def missing_keys(request: httpx.Request) -> httpx.Response:
            offset, limit = int(request.url.params['offset']), int(request.url.params['limit'])
            page = user_ids[offset:offset + limit]
            return httpx.Response(200, json={
                "range": {"offset": offset, "limit": limit, "total": len(user_ids)},
                "items": [{"userId": user_id, "fileId": NODE_ID} for user_id in page],
                "users": [{"id": user_id, "publicKeyContainer": public_key} for user_id in page],
                "files": [{"id": NODE_ID, "fileKeyContainer": get_file_key()}]
            })

        missing_keys_mock = respx.get(f'{API_URL}/nodes/missingFileKeys').mock(side_effect=missing_keys)
        set_keys_mock = respx.post(f'{API_URL}/nodes/files/keys').respond(204)

        await self.nodes.upload_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, plain_keypair=self.plain_keypair)

        assert [call.request.url.params['offset'] for call in missing_keys_mock.calls] == ['0', '50']
        batches = [json.loads(call.request.content)["items"] for call in set_keys_mock.calls]
        assert [len(batch) for batch in batches] == [50, 10]
        assert sorted(item["userId"] for batch in batches for item in batch) == user_ids

    @respx.mock
    async def test_upload_encrypted_chunked_content_range(self):
        upload_mock, _ = self.mock_proxy_upload()
        respx.get(f'{API_URL}/nodes/missingFileKeys').respond(200, json=self.missing_keys_empty_json)

        await self.nodes.upload_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                          plain_keypair=self.plain_keypair, chunksize=CHUNK_SIZE)

        content_ranges = [call.request.headers['Content-Range'] for call in upload_mock.calls]
        assert content_ranges == ['bytes 0-255/1000', 'bytes 256-511/1000', 'bytes 512-767/1000', 'bytes 768-999/1000']

    @respx.mock
    async def test_upload_encrypted_distributes_missing_file_keys(self):
        _, complete_mock = self.mock_proxy_upload()
        get_file_key = lambda: json.loads(complete_mock.calls.last.request.content)["fileKey"]
        set_keys_mock = self.mock_missing_keys_for_recipient(get_file_key)

        await self.nodes.upload_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel, plain_keypair=self.plain_keypair)

        assert set_keys_mock.called
        self.assert_recipient_file_key(set_keys_mock, get_file_key())

    # S3 direct uploads

    @respx.mock
    async def test_upload_s3_unencrypted_empty_file(self):
        self.file_path.write_bytes(b'')
        s3_urls_mock, s3_put_mock, complete_mock, _ = self.mock_s3_upload()

        with patch('dracoon.nodes.POLL_WAIT', 0):
            upload_status = await self.nodes.upload_s3_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel)

        assert json.loads(s3_urls_mock.calls.last.request.content) == {"firstPartNumber": 1, "lastPartNumber": 1, "size": 0}
        assert s3_put_mock.call_count == 1
        assert s3_put_mock.calls.last.request.content == b''
        assert s3_put_mock.calls.last.request.headers['Content-Length'] == '0'
        assert json.loads(complete_mock.calls.last.request.content)["parts"] == [{"partNumber": 1, "partEtag": "etag-1"}]
        assert upload_status.status == 'done'

    @respx.mock
    async def test_upload_s3_unencrypted_multipart(self):
        s3_urls_mock, s3_put_mock, complete_mock, status_mock = self.mock_s3_upload(
            status_responses=[self.upload_status_pending_json, self.upload_status_json])
        callback = CallbackRecorder()

        with patch('dracoon.nodes.POLL_WAIT', 0):
            upload_status = await self.nodes.upload_s3_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                                                   chunksize=CHUNK_SIZE, callback_fn=callback)

        # final (smaller) part is requested separately
        requested_parts = [json.loads(call.request.content) for call in s3_urls_mock.calls]
        assert requested_parts == [{"firstPartNumber": 4, "lastPartNumber": 4, "size": 232},
                                   {"firstPartNumber": 1, "lastPartNumber": 3, "size": 256}]
        assert [call.request.url.path.split('/')[-1] for call in s3_put_mock.calls] == ['1', '2', '3', '4']
        assert b''.join(call.request.content for call in s3_put_mock.calls) == self.data
        assert [call.request.headers['Content-Length'] for call in s3_put_mock.calls] == ['256', '256', '256', '232']
        assert 'Content-Length' not in self.dracoon.uploader.headers
        payload = json.loads(complete_mock.calls.last.request.content)
        assert payload == {"parts": [{"partNumber": part, "partEtag": f"etag-{part}"} for part in range(1, 5)],
                           "resolutionStrategy": "autorename", "fileName": "test.bin"}
        assert status_mock.call_count == 2
        assert upload_status.status == 'done'
        assert upload_status.node.id == NODE_ID
        assert callback.transferred == FILE_SIZE

    @respx.mock
    async def test_upload_s3_polling_wait_is_capped(self):
        self.mock_s3_upload(status_responses=[self.upload_status_pending_json] * 8 + [self.upload_status_json])

        with patch('dracoon.nodes.asyncio.sleep', new_callable=AsyncMock) as sleep_mock:
            upload_status = await self.nodes.upload_s3_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel)

        waits = [call.args[0] for call in sleep_mock.call_args_list]
        assert waits == [0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 5, 5]
        assert upload_status.status == 'done'

    @respx.mock
    async def test_upload_s3_polling_timeout(self):
        self.mock_s3_upload(status_responses=[self.upload_status_pending_json])

        with patch('dracoon.nodes.POLL_TIMEOUT', 0):
            with self.assertRaises(UploadTimeoutError):
                await self.nodes.upload_s3_unencrypted(file_path=str(self.file_path), upload_channel=self.upload_channel)

    @respx.mock
    async def test_upload_s3_encrypted_multipart(self):
        _, s3_put_mock, complete_mock, _ = self.mock_s3_upload()
        respx.get(f'{API_URL}/nodes/missingFileKeys').respond(200, json=self.missing_keys_empty_json)
        set_keys_mock = respx.post(f'{API_URL}/nodes/files/keys').respond(204)

        with patch('dracoon.nodes.POLL_WAIT', 0):
            upload_status = await self.nodes.upload_s3_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                                                 plain_keypair=self.plain_keypair, chunksize=CHUNK_SIZE)

        assert s3_put_mock.call_count == 4
        enc_data = b''.join(call.request.content for call in s3_put_mock.calls)
        payload = json.loads(complete_mock.calls.last.request.content)
        assert len(payload["parts"]) == 4
        self.assert_decrypts_to_data(enc_data, payload["fileKey"])
        assert not set_keys_mock.called
        assert upload_status.status == 'done'

    @respx.mock
    async def test_upload_s3_encrypted_distributes_missing_file_keys(self):
        _, _, complete_mock, _ = self.mock_s3_upload()
        get_file_key = lambda: json.loads(complete_mock.calls.last.request.content)["fileKey"]
        set_keys_mock = self.mock_missing_keys_for_recipient(get_file_key)

        with patch('dracoon.nodes.POLL_WAIT', 0):
            await self.nodes.upload_s3_encrypted(file_path=str(self.file_path), upload_channel=self.upload_channel,
                                                 plain_keypair=self.plain_keypair)

        assert set_keys_mock.called
        self.assert_recipient_file_key(set_keys_mock, get_file_key())


if __name__ == '__main__':
    unittest.main()
