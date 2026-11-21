import unittest
import asyncio
import base64
import json
from datetime import datetime, timedelta
from unittest.mock import patch
from urllib.parse import parse_qs

import httpx
import respx
from tenacity import wait_none

from dracoon.client import DRACOONClient, OAuth2ConnectionType
from dracoon.client.models import DRACOONConnection
from dracoon.nodes import DRACOONNodes
from dracoon.errors import (MissingCredentialsError, ConnectionError, HTTPBadRequestError, HTTPUnauthorizedError, HTTPPaymentRequiredError,
                            HTTPForbiddenError, HTTPNotFoundError, HTTPConflictError, HTTPPreconditionsFailedError,
                            HTTPTooManyRequestsError, HTTPUnknownError, HTTPServerError)

CLIENT_ID = 'client_id'
CLIENT_SECRET = 'client_secret'
BASE_URL = 'https://dracoon.team'
TOKEN_URL = f'{BASE_URL}/oauth/token'
REVOKE_URL = f'{BASE_URL}/oauth/revoke'

class TestDRACOONClient(unittest.TestCase):

    def test_client_creation_default_oauth(self):

        dracoon = DRACOONClient(base_url='https://just.a.test.com')

        self.assertEqual(dracoon.client_id, 'dracoon_legacy_scripting')
        self.assertEqual(dracoon.client_secret, '')
        self.assertFalse(dracoon.connected)


    def test_client_creation_custom_oauth(self):

        dracoon = DRACOONClient(base_url='https://just.a.test.com', client_id='my_test_client', client_secret='my_test_secret')

        self.assertEqual(dracoon.client_id, 'my_test_client')
        self.assertEqual(dracoon.client_secret, 'my_test_secret')
        self.assertFalse(dracoon.connected)

    def test_client_redirect_uri(self):
        dracoon_custom_redirect = DRACOONClient(base_url='https://foo.bar', redirect_uri='https://bar.foo/callback')
        dracoon_default_redirect = DRACOONClient(base_url='https://foo.bar')
        
        self.assertEqual(dracoon_custom_redirect.redirect_uri, 'https://bar.foo/callback')
        self.assertEqual(dracoon_default_redirect.redirect_uri, f"{dracoon_default_redirect.base_url}/oauth/callback")
        self.assertEqual(dracoon_custom_redirect.get_code_url(), f'{dracoon_custom_redirect.base_url}/oauth/authorize?branding=full&response_type=code&client_id={dracoon_custom_redirect.client_id}&redirect_uri=https://bar.foo/callback&scope=all')
        self.assertEqual(dracoon_default_redirect.get_code_url(), f'{dracoon_custom_redirect.base_url}/oauth/authorize?branding=full&response_type=code&client_id={dracoon_default_redirect.client_id}&redirect_uri=https://foo.bar/oauth/callback&scope=all')



def form_data(request: httpx.Request) -> dict:
    """ parse url encoded form body (token requests) into a flat dict """
    return {key: value[0] for key, value in parse_qs(request.content.decode()).items()}


class TestAsyncDRACOONClient(unittest.IsolatedAsyncioTestCase):

    def setUp(self) -> None:

        with open('tests/responses/auth/auth_ok.json', 'r') as json_file:
            self.auth_json = json.load(json_file)

        with open('tests/responses/auth/auth_error.json', 'r') as json_file:
            self.auth_error_json = json.load(json_file)

        with open('tests/responses/nodes/node_ok.json', 'r') as json_file:
            self.node_json = json.load(json_file)

        self.client = DRACOONClient(base_url=BASE_URL, client_id=CLIENT_ID, client_secret=CLIENT_SECRET)

        return super().setUp()

    async def asyncTearDown(self) -> None:
        await self.client.disconnect()

    def set_connection(self, connected_at: datetime, access_token: str = 'old_access_token', refresh_token: str = 'old_refresh_token'):
        """ simulate an established connection without a token request """
        self.client.connection = DRACOONConnection(connected_at, access_token, 3600, refresh_token)
        self.client.connected = True
        self.client.http.headers["Authorization"] = "Bearer " + access_token

    @respx.mock
    async def test_connect_password_flow(self):
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)

        connection = await self.client.connect(connection_type=OAuth2ConnectionType.password_flow, username='test_user', password='test_password')

        assert token_mock.called
        request = token_mock.calls.last.request
        assert form_data(request) == {'grant_type': 'password', 'username': 'test_user', 'password': 'test_password'}
        basic_auth = base64.b64encode(f'{CLIENT_ID}:{CLIENT_SECRET}'.encode('ascii')).decode('ascii')
        assert request.headers['Authorization'] == f'Basic {basic_auth}'
        assert connection.access_token == 'access_token'
        assert connection.refresh_token == 'refresh_token'
        assert connection.access_token_validity == 3600
        assert self.client.connected
        assert self.client.http.headers['Authorization'] == 'Bearer access_token'

    @respx.mock
    async def test_connect_auth_code_flow(self):
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)

        await self.client.connect(connection_type=OAuth2ConnectionType.auth_code, auth_code='auth_code', redirect_uri='https://custom.redirect/callback')

        assert token_mock.called
        assert form_data(token_mock.calls.last.request) == {'grant_type': 'authorization_code', 'code': 'auth_code', 'client_id': CLIENT_ID,
                                                            'client_secret': CLIENT_SECRET, 'redirect_uri': 'https://custom.redirect/callback'}
        assert self.client.redirect_uri == 'https://custom.redirect/callback'
        assert self.client.http.headers['Authorization'] == 'Bearer access_token'

    @respx.mock
    async def test_connect_refresh_token_from_connection(self):
        self.set_connection(datetime.now())
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)

        connection = await self.client.connect(connection_type=OAuth2ConnectionType.refresh_token)

        assert form_data(token_mock.calls.last.request) == {'grant_type': 'refresh_token', 'refresh_token': 'old_refresh_token',
                                                            'client_id': CLIENT_ID, 'client_secret': CLIENT_SECRET}
        assert connection.access_token == 'access_token'
        assert self.client.http.headers['Authorization'] == 'Bearer access_token'

    @respx.mock
    async def test_connect_refresh_token_provided(self):
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)

        await self.client.connect(connection_type=OAuth2ConnectionType.refresh_token, refresh_token='provided_refresh_token')

        assert form_data(token_mock.calls.last.request)['refresh_token'] == 'provided_refresh_token'

    async def test_connect_missing_credentials(self):
        for connection_type in OAuth2ConnectionType:
            with self.subTest(connection_type=connection_type):
                client = DRACOONClient(base_url=BASE_URL)
                with self.assertRaises(MissingCredentialsError):
                    await client.connect(connection_type=connection_type)

    @respx.mock
    async def test_connect_password_flow_missing_password(self):
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)

        with self.assertRaises(MissingCredentialsError):
            await self.client.connect(connection_type=OAuth2ConnectionType.password_flow, username='test_user')

        assert not token_mock.called

    @respx.mock
    async def test_connect_unauthorized(self):
        respx.post(TOKEN_URL).respond(401, json=self.auth_error_json)

        with self.assertRaises(HTTPUnauthorizedError):
            await self.client.connect(connection_type=OAuth2ConnectionType.password_flow, username='test_user', password='wrong_password')

        assert not self.client.connected

    @respx.mock
    async def test_connect_connection_error(self):
        respx.post(TOKEN_URL).mock(side_effect=httpx.ConnectError)

        with self.assertRaises(ConnectionError):
            await self.client.connect(connection_type=OAuth2ConnectionType.password_flow, username='test_user', password='test_password')

    def test_raise_http_error(self):
        cases = {
            400: HTTPBadRequestError,
            401: HTTPUnauthorizedError,
            402: HTTPPaymentRequiredError,
            403: HTTPForbiddenError,
            404: HTTPNotFoundError,
            409: HTTPConflictError,
            412: HTTPPreconditionsFailedError,
            429: HTTPTooManyRequestsError,
            500: HTTPUnknownError,
            502: HTTPServerError,
            503: HTTPServerError,
            418: HTTPUnknownError,
        }
        for status_code, error in cases.items():
            with self.subTest(status_code=status_code):
                request = httpx.Request('GET', BASE_URL)
                response = httpx.Response(status_code, request=request)
                http_error = httpx.HTTPStatusError('error', request=request, response=response)

                with self.assertRaises(error) as raised:
                    self.client.raise_http_error(err=http_error)

                assert raised.exception.error is http_error

    @respx.mock
    async def test_logout(self):
        self.set_connection(datetime.now())
        revoke_mock = respx.post(REVOKE_URL).respond(200)

        await self.client.logout()

        assert revoke_mock.call_count == 1
        data = form_data(revoke_mock.calls.last.request)
        assert data['token'] == 'old_access_token'
        assert data['token_type_hint'] == 'access_token'
        assert not self.client.connected
        assert self.client.connection is None

    @respx.mock
    async def test_logout_revoke_refresh_token(self):
        self.set_connection(datetime.now())
        revoke_mock = respx.post(REVOKE_URL).respond(200)

        await self.client.logout(revoke_refresh_token=True)

        assert revoke_mock.call_count == 2
        revoked = [form_data(call.request) for call in revoke_mock.calls]
        assert [data['token_type_hint'] for data in revoked] == ['access_token', 'refresh_token']
        assert revoked[1]['token'] == 'old_refresh_token'

    async def test_check_access_token(self):
        self.set_connection(datetime.now())
        assert await self.client.check_access_token()

        self.set_connection(datetime.now() - timedelta(hours=2))
        assert not await self.client.check_access_token()

    async def test_check_access_token_expired_days_ago(self):
        self.set_connection(datetime.now() - timedelta(days=1, seconds=10))
        assert not await self.client.check_access_token()

    @respx.mock
    async def test_expired_token_is_refreshed_before_request(self):
        self.set_connection(datetime.now() - timedelta(hours=2))
        token_mock = respx.post(TOKEN_URL).respond(200, json=self.auth_json)
        node_mock = respx.get(f'{BASE_URL}/api/v4/nodes/2').respond(200, json=self.node_json)
        nodes = DRACOONNodes(self.client)

        node = await nodes.get_node(node_id=2)

        assert node.id == 2
        assert form_data(token_mock.calls.last.request)['grant_type'] == 'refresh_token'
        assert node_mock.calls.last.request.headers['Authorization'] == 'Bearer access_token'

    @respx.mock
    async def test_concurrent_requests_refresh_token_once(self):
        self.set_connection(datetime.now() - timedelta(hours=2))

        async def token_response(request: httpx.Request) -> httpx.Response:
            # yield to the event loop like a real network request
            await asyncio.sleep(0)
            return httpx.Response(200, json=self.auth_json)

        token_mock = respx.post(TOKEN_URL).mock(side_effect=token_response)
        node_mock = respx.get(f'{BASE_URL}/api/v4/nodes/2').respond(200, json=self.node_json)
        nodes = DRACOONNodes(self.client)

        results = await asyncio.gather(*[nodes.get_node(node_id=2) for _ in range(5)])

        assert all(node.id == 2 for node in results)
        assert token_mock.call_count == 1
        assert all(call.request.headers['Authorization'] == 'Bearer access_token' for call in node_mock.calls)

    @respx.mock
    async def test_retry_on_too_many_requests(self):
        self.client.raise_on_err = True
        self.set_connection(datetime.now())
        node_mock = respx.get(f'{BASE_URL}/api/v4/nodes/2').mock(side_effect=[httpx.Response(429), httpx.Response(200, json=self.node_json)])
        nodes = DRACOONNodes(self.client)

        with patch.object(DRACOONNodes.get_node.retry, 'wait', wait_none()):
            node = await nodes.get_node(node_id=2)

        assert node.id == 2
        assert node_mock.call_count == 2


if __name__ == '__main__':
    unittest.main()