import unittest

from dracoon.shares import DRACOONShares
from tests.adapter_harness import make_client


class TestShareMakers(unittest.TestCase):
    """ payload makers must not drop fields (pydantic ignores unknown keys) """

    def setUp(self):
        self.shares = DRACOONShares(make_client())

    def test_shares_update(self):
        shares_update = self.shares.make_shares_update(shares_list=[1, 2], max_downloads=3)
        self.assertEqual(shares_update.objectIds, [1, 2])
        self.assertEqual(shares_update.maxDownloads, 3)

    def test_share_update_sms_recipients(self):
        share_update = self.shares.make_share_update(sms_recipients=['+491234'])
        self.assertEqual(share_update.textMessageRecipients, ['+491234'])

    def test_file_request(self):
        file_request = self.shares.make_file_request(target_id=1, language='de-DE', file_expiration=7)
        self.assertEqual(file_request.receiverLanguage, 'de-DE')
        self.assertEqual(file_request.filesExpiryPeriod, 7)

    def test_file_request_update(self):
        file_request_update = self.shares.make_file_request_update(language='de-DE', reset_max_slots=True, reset_max_size=True)
        payload = file_request_update.model_dump(exclude_unset=True)
        self.assertEqual(payload, {"receiverLanguage": 'de-DE', "resetMaxSlots": True, "resetMaxSize": True})

    def test_file_requests_update(self):
        file_requests_update = self.shares.make_file_requests_update(file_requests_list=[1, 2], reset_max_slots=True)
        payload = file_requests_update.model_dump(exclude_unset=True)
        self.assertEqual(payload, {"objectIds": [1, 2], "resetMaxSlots": True, "resetMaxSize": True})


if __name__ == '__main__':
    unittest.main()
