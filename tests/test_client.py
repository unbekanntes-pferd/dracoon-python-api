import unittest
from dracoon.client import DRACOONClient

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
        self.assertEqual(dracoon_custom_redirect.get_code_url(), dracoon_custom_redirect.base_url + f'/oauth/authorize?branding=full&response_type=code&client_id={dracoon_custom_redirect.client_id}&redirect_uri=https://bar.foo/callback&scope=all')
        self.assertEqual(dracoon_default_redirect.get_code_url(), dracoon_custom_redirect.base_url + f'/oauth/authorize?branding=full&response_type=code&client_id={dracoon_default_redirect.client_id}&redirect_uri=https://foo.bar/oauth/callback&scope=all')

if __name__ == '__main__':
    unittest.main()