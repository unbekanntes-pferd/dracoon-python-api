import unittest
import sys
from dracoon import crypto
from dracoon.crypto.models import FileKey, FileKeyVersion, PlainFileKey, PlainFileKeyVersion, PlainUserKeyPairContainer, UserKeyPairContainer, UserKeyPairVersion

class TestDRACOONCrypto(unittest.TestCase):
    """ Test cases for the DRACOON Python Crypto package """

    def test_plain_user_keypair_generation_2048(self):
        """ tests function to create a plain RSA 2048 keypair """
        plain_keypair = crypto.create_plain_userkeypair(version=UserKeyPairVersion.RSA2048)
        self.assertIsInstance(plain_keypair, PlainUserKeyPairContainer)
        self.assertEqual(plain_keypair.privateKeyContainer.version, UserKeyPairVersion.RSA2048.value)
        self.assertEqual(plain_keypair.publicKeyContainer.version, UserKeyPairVersion.RSA2048.value)

    def test_plain_user_keypair_generation_4096(self):
        """ tests function to create a plain RSA 4096 keypair """
        plain_keypair = crypto.create_plain_userkeypair(version=UserKeyPairVersion.RSA4096)
        self.assertIsInstance(plain_keypair, PlainUserKeyPairContainer)
        self.assertEqual(plain_keypair.privateKeyContainer.version, UserKeyPairVersion.RSA4096.value)
        self.assertEqual(plain_keypair.publicKeyContainer.version, UserKeyPairVersion.RSA4096.value)

    def test_private_key_encryption(self):

        """ Test en- and decryption of a private key with given secret """

        secret = 'VerySecret1234!'
        plain_2048_keypair = crypto.create_plain_userkeypair(version=UserKeyPairVersion.RSA2048)
        plain_4096_keypair = crypto.create_plain_userkeypair(version=UserKeyPairVersion.RSA4096)
        encrypted_2048_keypair = crypto.encrypt_private_key(secret=secret, plain_key=plain_2048_keypair)
        encrypted_4096_keypair = crypto.encrypt_private_key(secret=secret, plain_key=plain_4096_keypair)

        self.assertIsInstance(encrypted_2048_keypair, UserKeyPairContainer)
        self.assertIsInstance(encrypted_4096_keypair, UserKeyPairContainer)
        self.assertNotEqual(plain_2048_keypair, encrypted_2048_keypair)
        self.assertNotEqual(plain_4096_keypair, encrypted_4096_keypair)

        decrypted_2048_keypair = crypto.decrypt_private_key(secret=secret, keypair=encrypted_2048_keypair)
        decrypted_4096_keypair = crypto.decrypt_private_key(secret=secret, keypair=encrypted_4096_keypair)

        self.assertEqual(plain_2048_keypair, decrypted_2048_keypair)
        self.assertEqual(plain_4096_keypair, decrypted_4096_keypair)


    def test_encryption_on_the_fly(self):
        """ Test en- and decryption on the fly with given plain file keys """

        plain_2048_file_key = crypto.create_file_key(version=PlainFileKeyVersion.AES256GCM)
        plain_4096_file_key = crypto.create_file_key(version=PlainFileKeyVersion.AES256GCM)

        message = b'Very secret message'

        message_enc_2048, plain_key_2048 = crypto.encrypt_bytes(plain_data=message, plain_file_key=plain_2048_file_key)
        message_enc_4096, plain_key_4096 = crypto.encrypt_bytes(plain_data=message, plain_file_key=plain_4096_file_key)

        """ Message no longer readable """
        self.assertNotEqual(message_enc_2048, message)
        self.assertNotEqual(message_enc_4096, message)
        
        """ After finalizing, the key contains a tag """
        self.assertIsNotNone(plain_key_2048.tag)
        self.assertIsNotNone(plain_key_4096.tag)
        
        """ Decrypting the message with obtained file key should deliver the same message """
        decrypted_2048 = crypto.decrypt_bytes(enc_data=message_enc_2048, plain_file_key=plain_key_2048)
        decrypted_4096 = crypto.decrypt_bytes(enc_data=message_enc_4096, plain_file_key=plain_key_4096)

        """ Plain keys should adhere to format """
        self.assertIsInstance(plain_key_2048, PlainFileKey)
        self.assertIsInstance(plain_key_4096, PlainFileKey)
        
        """ Plain keys be equal, as tag has been added after encryption – received key is returned and updated """
        self.assertEqual(plain_2048_file_key, plain_key_2048)
        self.assertEqual(plain_4096_file_key, plain_key_4096)
        
        """ Ensure original message is received """
        self.assertEqual(message, decrypted_2048)
        self.assertEqual(message, decrypted_4096)

    def test_chunked_encryption(self):
        """ Test chunked en- and decryption with given plain file keys """

        plain_2048_file_key = crypto.create_file_key(version=PlainFileKeyVersion.AES256GCM)
        plain_4096_file_key = crypto.create_file_key(version=PlainFileKeyVersion.AES256GCM)

        message = 'Very secret message'

        encryptor_2048 = crypto.FileEncryptionCipher(plain_file_key=plain_2048_file_key)
        encryptor_4096 = crypto.FileEncryptionCipher(plain_file_key=plain_4096_file_key)

        message_enc_2048 = b''
        message_enc_4096 = b''

        """ Encrypt each character """
        for char in message:
            buf = char.encode()
            message_enc_2048 += encryptor_2048.encode_bytes(plain_data=buf)
            message_enc_4096 += encryptor_4096.encode_bytes(plain_data=buf)

        """ Finalize encryption """
        last_data_2048, plain_2048_key = encryptor_2048.finalize()
        last_data_4096, plain_4096_key = encryptor_4096.finalize()

        message_enc_2048 += last_data_2048
        message_enc_4096 += last_data_4096
         
        """ Ensure message is no longer readable """
        self.assertNotEqual(message_enc_2048, message)
        self.assertNotEqual(message_enc_4096, message)
        
        decryptor_2048 = crypto.FileDecryptionCipher(plain_file_key=plain_2048_key)
        decryptor_4096 = crypto.FileDecryptionCipher(plain_file_key=plain_4096_key)

        message_2048 = b''
        message_4096 = b''


        for chunk in message_enc_2048:
            chunk = chunk.to_bytes(1, sys.byteorder)      
            message_2048 += decryptor_2048.decode_bytes(chunk)
            
        for chunk in message_enc_4096:
            chunk = chunk.to_bytes(1, sys.byteorder)      
            message_4096 += decryptor_4096.decode_bytes(chunk)
        
        
        message_2048 += decryptor_2048.finalize()
        message_4096 += decryptor_4096.finalize()

        decrypted_2048_fly = crypto.decrypt_bytes(enc_data=message_enc_2048, plain_file_key=plain_2048_key)
        decrypted_4096_fly = crypto.decrypt_bytes(enc_data=message_enc_4096, plain_file_key=plain_4096_key)

        self.assertEqual(message_2048, decrypted_2048_fly)
        self.assertEqual(message_4096, decrypted_4096_fly)

        self.assertEqual(message.encode(), message_2048)
        self.assertEqual(message.encode(), message_4096)


    def test_file_key_encryption(self):
        """ Test encryption of a plain file key for both versions, ensure version check correct """
        plain_file_key_2048 = crypto.create_file_key(PlainFileKeyVersion.AES256GCM)
        plain_file_key_4096 = crypto.create_file_key(PlainFileKeyVersion.AES256GCM)
        plain_keypair_2048 = crypto.create_plain_userkeypair(UserKeyPairVersion.RSA2048)
        plain_keypair_4096 = crypto.create_plain_userkeypair(UserKeyPairVersion.RSA4096)

        enc_file_key_2048 = crypto.encrypt_file_key(plain_file_key=plain_file_key_2048, keypair=plain_keypair_2048)
        enc_file_key_4096 = crypto.encrypt_file_key(plain_file_key=plain_file_key_4096, keypair=plain_keypair_4096)

        self.assertIsInstance(enc_file_key_2048, FileKey)
        self.assertIsInstance(enc_file_key_4096, FileKey)

        self.assertEqual(enc_file_key_2048.version, FileKeyVersion.RSA2048_AES256GCM.value)
        self.assertEqual(enc_file_key_4096.version, FileKeyVersion.RSA_4096_AES256GCM.value)

        decrypted_key_2048 = crypto.decrypt_file_key(file_key=enc_file_key_2048, keypair=plain_keypair_2048)
        decrypted_key_4096 = crypto.decrypt_file_key(file_key=enc_file_key_4096, keypair=plain_keypair_4096)

        self.assertEqual(plain_file_key_2048, decrypted_key_2048)
        self.assertEqual(plain_file_key_4096, decrypted_key_4096)

        self.assertIsInstance(decrypted_key_2048, PlainFileKey)
        self.assertIsInstance(decrypted_key_4096, PlainFileKey)
        
    def test_public_file_key_encrytion(self):
        """ Test encryption of a plain file key for both versions using a public key """
        plain_file_key_2048 = crypto.create_file_key(PlainFileKeyVersion.AES256GCM)
        plain_file_key_4096 = crypto.create_file_key(PlainFileKeyVersion.AES256GCM)
        
        plain_keypair_2048 = crypto.create_plain_userkeypair(UserKeyPairVersion.RSA2048)
        plain_keypair_4096 = crypto.create_plain_userkeypair(UserKeyPairVersion.RSA4096)

        enc_file_key_2048 = crypto.encrypt_file_key_public(public_key=plain_keypair_2048.publicKeyContainer, plain_file_key=plain_file_key_2048)
        enc_file_key_4096 = crypto.encrypt_file_key_public(public_key=plain_keypair_4096.publicKeyContainer, plain_file_key=plain_file_key_4096)

        self.assertIsInstance(enc_file_key_2048, FileKey)
        self.assertIsInstance(enc_file_key_4096, FileKey)

        self.assertEqual(enc_file_key_2048.version, FileKeyVersion.RSA2048_AES256GCM.value)
        self.assertEqual(enc_file_key_4096.version, FileKeyVersion.RSA_4096_AES256GCM.value)

        decrypted_key_2048 = crypto.decrypt_file_key(file_key=enc_file_key_2048, keypair=plain_keypair_2048)
        decrypted_key_4096 = crypto.decrypt_file_key(file_key=enc_file_key_4096, keypair=plain_keypair_4096)

        self.assertEqual(plain_file_key_2048, decrypted_key_2048)
        self.assertEqual(plain_file_key_4096, decrypted_key_4096)

        self.assertIsInstance(decrypted_key_2048, PlainFileKey)
        self.assertIsInstance(decrypted_key_4096, PlainFileKey)
        

if __name__ == '__main__':
    unittest.main()