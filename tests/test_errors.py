import unittest
from dracoon.errors import * 

class TestDRACOONErrors(unittest.TestCase):
    """ Test cases for the DRACOON Python errors """

    def test_base_error(self):
        """ tests DRACOON base error """
        message = "oops"
        base_error = DRACOONBaseError(message=message)
        self.assertIsInstance(base_error, DRACOONBaseError)
        self.assertIsInstance(base_error, Exception)
        self.assertEqual(base_error.message, message)
        
    def test_crypto_error(self):
        """ tests DRACOON crypto error """
        message = "oops crypto"
        crypto_error = DRACOONCryptoError(message=message)
        self.assertIsInstance(crypto_error, DRACOONCryptoError)
        self.assertIsInstance(crypto_error, DRACOONBaseError)
        self.assertEqual(crypto_error.message, message)

    def test_client_error(self):
        """ tests DRACOON client error """
        message = "oops client"
        client_error = DRACOONClientError(message=message)
        self.assertIsInstance(client_error, DRACOONClientError)
        self.assertIsInstance(client_error, DRACOONBaseError)
        self.assertEqual(client_error.message, message)
        
    def test_validation_error(self):
        """ tests DRACOON validation error """
        message = "oops validation"
        validation_error = DRACOONValidationError(message=message)
        self.assertIsInstance(validation_error, DRACOONValidationError)
        self.assertIsInstance(validation_error, DRACOONBaseError)
        self.assertEqual(validation_error.message, message)

    def test_http_error(self):
        """ tests DRACOON http error """
        message = "oops http"
        http_error = DRACOONHttpError(message=message, error="mock error")
        self.assertIsInstance(http_error, DRACOONHttpError)
        self.assertIsInstance(http_error, DRACOONBaseError)
        self.assertEqual(http_error.message, message)
        self.assertEqual(http_error.error, "mock error")
        self.assertEqual(http_error.is_xml, False)

if __name__ == '__main__':
    unittest.main()