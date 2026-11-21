"""
Known-answer tests against official DRACOON crypto test vectors (see tests/responses/crypto/README.md).
Verifies interoperability with other DRACOON clients, not just self-consistency.
"""
import unittest
import base64
import json
from pathlib import Path

from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import padding

from dracoon.crypto import decrypt_private_key, decrypt_file_key, decrypt_bytes, encrypt_file_key_public, create_file_key
from dracoon.crypto.models import UserKeyPairContainer, FileKey, PlainFileKey, PlainFileKeyVersion, PublicKeyContainer

VECTORS = Path('tests/responses/crypto')

# OAEP parameters per keypair version as implemented by the DRACOON reference SDKs (Java Crypto.java)
REFERENCE_OAEP = {
    'kp_rsa2048': padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA1()), algorithm=hashes.SHA256(), label=None),
    'kp_rsa4096': padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()), algorithm=hashes.SHA256(), label=None),
}


def load_json(path: str) -> dict:
    with open(VECTORS / path, 'r') as json_file:
        return json.load(json_file)


def load_keypair(name: str) -> UserKeyPairContainer:
    return UserKeyPairContainer(privateKeyContainer=load_json(f'{name}/private_key.json'),
                                publicKeyContainer=load_json(f'{name}/public_key.json'))


def load_password(name: str) -> str:
    return (VECTORS / name / 'pw.txt').read_text()


def load_plain_file_key(name: str) -> PlainFileKey:
    plain_file_key = load_json(f'{name}/plain_file_key.json')
    # reference data uses legacy version 'A' for plain file keys
    plain_file_key['version'] = PlainFileKeyVersion.AES256GCM.value
    return PlainFileKey(**plain_file_key)


class TestDRACOONCryptoVectors(unittest.TestCase):

    def assert_decrypt_private_key(self, name: str):
        keypair = load_keypair(name)
        plain_keypair = decrypt_private_key(load_password(name), keypair)

        private_key = serialization.load_pem_private_key(plain_keypair.privateKeyContainer.privateKey.encode('ascii'), password=None)
        public_key = serialization.load_pem_public_key(keypair.publicKeyContainer.publicKey.encode('ascii'))
        assert private_key.public_key().public_numbers() == public_key.public_numbers()

    def assert_decrypt_file_key(self, keypair_name: str, file_key_name: str):
        plain_keypair = decrypt_private_key(load_password(keypair_name), load_keypair(keypair_name))
        enc_file_key = FileKey(**load_json(f'{file_key_name}/enc_file_key.json'))

        plain_file_key = decrypt_file_key(enc_file_key, plain_keypair)

        expected = load_plain_file_key(file_key_name)
        assert plain_file_key.key == expected.key
        assert plain_file_key.iv == expected.iv
        assert plain_file_key.tag == expected.tag

    def assert_encrypt_file_key_public(self, keypair_name: str):
        """ file key encrypted by this library must be decryptable with the reference OAEP parameters """
        keypair = load_keypair(keypair_name)
        plain_file_key = create_file_key()

        file_key = encrypt_file_key_public(plain_file_key, PublicKeyContainer(**keypair.publicKeyContainer.model_dump()))

        private_key = serialization.load_pem_private_key(keypair.privateKeyContainer.privateKey.encode('ascii'),
                                                         password=load_password(keypair_name).encode('ascii'))
        plain_key = private_key.decrypt(base64.b64decode(file_key.key), REFERENCE_OAEP[keypair_name])
        assert base64.b64encode(plain_key).decode('ascii') == plain_file_key.key

    def test_decrypt_private_key_rsa2048(self):
        self.assert_decrypt_private_key('kp_rsa2048')

    def test_decrypt_private_key_rsa4096(self):
        self.assert_decrypt_private_key('kp_rsa4096')

    def test_decrypt_private_key_wrong_password(self):
        with self.assertRaises(ValueError):
            decrypt_private_key('wrong password', load_keypair('kp_rsa4096'))

    @unittest.expectedFailure
    def test_decrypt_file_key_rsa2048(self):
        # known bug: RSA-2048 (version A) uses OAEP hash SHA-1 / MGF1 SHA-256 - reference is hash SHA-256 / MGF1 SHA-1
        self.assert_decrypt_file_key('kp_rsa2048', 'fk_rsa2048_aes256gcm')

    def test_decrypt_file_key_rsa4096(self):
        self.assert_decrypt_file_key('kp_rsa4096', 'fk_rsa4096_aes256gcm')

    @unittest.expectedFailure
    def test_encrypt_file_key_public_rsa2048(self):
        # known bug: see test_decrypt_file_key_rsa2048
        self.assert_encrypt_file_key_public('kp_rsa2048')

    def test_encrypt_file_key_public_rsa4096(self):
        self.assert_encrypt_file_key_public('kp_rsa4096')

    def test_decrypt_file(self):
        enc_file = base64.b64decode((VECTORS / 'files/aes256gcm/enc_file.b64').read_text())
        plain_file = base64.b64decode((VECTORS / 'files/plain_file.b64').read_text())

        plain_bytes = decrypt_bytes(enc_file, load_plain_file_key('fk_rsa2048_aes256gcm'))

        assert plain_bytes == plain_file


if __name__ == '__main__':
    unittest.main()
