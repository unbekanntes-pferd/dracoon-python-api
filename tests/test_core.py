from dracoon.core import DRACOONClient, DRACOONConnection, OAuth2ConnectionType
import unittest
import dotenv
import os


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

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

    
class TestAsyncDRACOONClient(unittest.IsolatedAsyncioTestCase):
    async def test_connection_offline(self):

        dracoon = DRACOONClient(base_url='https://just.a.test.com', client_id='my_test_client', client_secret='my_test_secret')

        self.assertFalse(await dracoon.test_connection())

    
    async def test_connection_password_flow(self):

        dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        self.assertTrue(await dracoon.test_connection())
        self.assertIsNotNone(dracoon.connection)
        self.assertIsInstance(dracoon.connection, DRACOONConnection)
        self.assertTrue(dracoon.connected)

        await dracoon.logout(revoke_refresh_token=True)

    
    async def test_refresh_token_auth(self):

        dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        connection1 = await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
        connection2 = await dracoon.connect(OAuth2ConnectionType.refresh_token)

        self.assertIsInstance(connection1, DRACOONConnection)
        self.assertIsInstance(connection2, DRACOONConnection)

        self.assertNotEqual(connection1, connection2)
        self.assertTrue(await dracoon.test_connection())
        self.assertTrue(dracoon.connected)

        await dracoon.logout(revoke_refresh_token=True)

    async def test_logout(self):
        dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        await dracoon.logout()

        self.assertFalse(dracoon.connected)
        self.assertIsNone(dracoon.connection)

    
    async def test_access_token_validity(self):
        dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        access_token_valid_no_test = await dracoon.check_access_token()
        access_token_valid_test = await dracoon.check_access_token(test=True)

        self.assertTrue(access_token_valid_no_test)
        self.assertTrue(access_token_valid_test)

        await dracoon.logout()

    async def test_refresh_token_validity(self):
        dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)

        await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)

        refresh_token_valid = dracoon.check_refresh_token()

        self.assertTrue(refresh_token_valid)

        await dracoon.logout()


if __name__ == '__main__':
    unittest.main()