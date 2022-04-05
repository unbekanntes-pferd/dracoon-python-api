
"""
DRACOON Crypto utils based on cryptography
V1.2.0

(c) Octavio Simone, November 2021 

Collection of DRACOON API calls
Documentation: https://dracoon.team/api

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 
 
Encryption: 
 - Files are encrypted with AES 256 GCM cipher
 - Keypair (public and private key) is RSA-4096 (2048 supported as well)

"""
import os
import base64
import logging 
from typing import Tuple

from pydantic import validate_arguments
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import (Cipher, algorithms, modes)


from dracoon.errors import (InvalidKeypairVersionError, FileKeyEncryptionError, CryptoMissingDataError, InvalidFileKeyError)
from .models import (FileKey, FileKeyVersion, PlainFileKey, PlainFileKeyVersion,  
                                   PlainUserKeyPairContainer, PublicKeyContainer, UserKeyPairContainer, 
                                   UserKeyPairVersion)

logger = logging.getLogger('dracoon.crypto')

@validate_arguments
def encrypt_private_key(secret: str, plain_key: PlainUserKeyPairContainer) -> UserKeyPairContainer:
    """ encrypt a private key (requires a plain user keypair container: create_plain_user_keypair()) """
    logger.info("Encrypting private key - version: %s", plain_key.privateKeyContainer.version)
    # load plain private key
    private_key_pem = plain_key.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(
        data=private_key_pem.encode('ascii'), password=None)

    # serialize key with passphrase (secret)
    encrypted_private_key = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                      format=serialization.PrivateFormat.PKCS8,
                                                      encryption_algorithm=serialization.BestAvailableEncryption(secret.encode('ascii')))

    return UserKeyPairContainer(**{

        "privateKeyContainer": {
            "version": plain_key.privateKeyContainer.version,
            "privateKey": encrypted_private_key.decode('ascii')
        },
        "publicKeyContainer": {
            "version": plain_key.publicKeyContainer.version,
            "publicKey": plain_key.publicKeyContainer.publicKey
        }
    })

@validate_arguments
def decrypt_private_key(secret: str, keypair: UserKeyPairContainer) -> PlainUserKeyPairContainer:
    """ decrypt a private key (requires secret). Returns a plain user keypair """
    logger.info("Decrypting private key - version: %s", keypair.privateKeyContainer.version)
    # load encrypted private key
    private_key_pem = keypair.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(
        data=private_key_pem.encode('ascii'), password=secret.encode('ascii'), )

    # export without passphrase
    private_key_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                                format=serialization.PrivateFormat.TraditionalOpenSSL,
                                                encryption_algorithm=serialization.NoEncryption())

    return PlainUserKeyPairContainer(**{

        "privateKeyContainer": {
            "version": keypair.privateKeyContainer.version,
            "privateKey": private_key_pem.decode('ascii')
        },
        "publicKeyContainer": {
            "version": keypair.publicKeyContainer.version,
            "publicKey": keypair.publicKeyContainer.publicKey
        }
    })


@validate_arguments
def create_plain_userkeypair(version: UserKeyPairVersion) -> PlainUserKeyPairContainer:
    """ create a new RSA plain keypair – needs to be encrypted with encrypt_private_key() """
    
    logger.info("Creating plain user keypair - version: %s", version.value)

    # generate asymmetric RSA key based on version
    if version == UserKeyPairVersion.RSA2048:
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    elif version == UserKeyPairVersion.RSA4096:
        key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
    else:
        raise InvalidKeypairVersionError(message='Invalid keypair version')
    private_key_pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                                        format=serialization.PrivateFormat.TraditionalOpenSSL,
                                        encryption_algorithm=serialization.NoEncryption())
    public_key = key.public_key()
    public_key_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)

    return PlainUserKeyPairContainer(**{

        "privateKeyContainer": {
            "version": version.value,
            "privateKey": private_key_pem.decode('ascii')
        },
        "publicKeyContainer": {
            "version": version.value,
            "publicKey": public_key_pem.decode('ascii')
        }
    })


def get_file_key_version(keypair: PlainUserKeyPairContainer) -> FileKeyVersion:
    """ get required file key version from given user keypair """

    logger.info("Getting file key version: %s", keypair.privateKeyContainer.version)

    if keypair.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value and keypair.privateKeyContainer.version == UserKeyPairVersion.RSA2048.value:
        return FileKeyVersion.RSA2048_AES256GCM
    elif keypair.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value and keypair.privateKeyContainer.version == UserKeyPairVersion.RSA4096.value:
        return FileKeyVersion.RSA_4096_AES256GCM
    else:
        raise InvalidKeypairVersionError(message='Invalid keypair version')


def get_file_key_version_public(public_key: PublicKeyContainer) -> FileKeyVersion:
    """ get file required file key version from given public key (needed for missing file keys request) """
    
    logger.info("Getting file key version: %s", public_key.version)

    if public_key.version == UserKeyPairVersion.RSA2048.value:
        return FileKeyVersion.RSA2048_AES256GCM
    elif public_key.version == UserKeyPairVersion.RSA4096.value:
        return FileKeyVersion.RSA_4096_AES256GCM
    else:
        raise InvalidKeypairVersionError(message='Invalid keypair version')


@validate_arguments
def create_file_key(version: PlainFileKeyVersion = PlainFileKeyVersion.AES256GCM) -> PlainFileKey:
    """ create a plain file key (AES 256) """

    logger.info("Creating file key: %s", version.value)

    # get random bytes for key and vector
    key = os.urandom(32)
    iv = os.urandom(12)

    # base64 encode
    encoded_key = base64.b64encode(key)
    encoded_iv = base64.b64encode(iv)

    return PlainFileKey(**{
        "version": version.value,
        "key": encoded_key.decode('ascii'),
        "iv": encoded_iv.decode('ascii'),
        "tag": None
    })


def encrypt_file_key_public(plain_file_key: PlainFileKey, public_key: PublicKeyContainer) -> FileKey:
    """ encrypt a file key with given public key container """

    logger.info("Creating file key with public key: %s", public_key.version)

    public_key_pem = serialization.load_pem_public_key(
        public_key.publicKey.encode('ascii'))
        
    # check correct version
    file_key_version = get_file_key_version_public(public_key)

    key = plain_file_key.key

    # initialize variable for encrypted file key
    encrypted_key = None

    # use SHA1 MGF1 and SHA256 hash
    if public_key.version == UserKeyPairVersion.RSA2048.value:
        encrypted_key = public_key_pem.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                                     algorithm=hashes.SHA1(),
                                                                                                     label=None))
    # use SHA256 (hash and MGF1)
    elif public_key.version == UserKeyPairVersion.RSA4096.value:
        encrypted_key = public_key_pem.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                                     algorithm=hashes.SHA256(),
                                                                                                     label=None))
    return FileKey(**{
        "version": file_key_version.value,
        "key": base64.b64encode(encrypted_key).decode(),
        "iv": plain_file_key.iv,
        "tag": plain_file_key.tag
    })

# encrypt a plain file key


def encrypt_file_key(plain_file_key: PlainFileKey, keypair: PlainUserKeyPairContainer) -> FileKey: 
    """ encrypt a file key with given plain user keypair """

    logger.info("Encrypting file key: %s", keypair.privateKeyContainer.version)

    private_key_pem = keypair.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(
        data=private_key_pem.encode('ascii'), password=None)
    public_key = private_key.public_key()

    # check correct version
    file_key_version = get_file_key_version(keypair)

    key = plain_file_key.key

    # initialize variable for encrypted file key
    encrypted_key = None

    # use SHA1 MGF1 and SHA256 hash
    if keypair.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value:
        encrypted_key = public_key.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                                 algorithm=hashes.SHA1(),
                                                                                                 label=None))
    # use SHA256 (hash and MGF1)
    elif keypair.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value:
        encrypted_key = public_key.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                                 algorithm=hashes.SHA256(),
                                                                                                 label=None))
    return FileKey(**{
        "version": file_key_version.value,
        "key": base64.b64encode(encrypted_key).decode(),
        "iv": plain_file_key.iv,
        "tag": plain_file_key.tag
    })


def decrypt_file_key(file_key: FileKey, keypair: PlainUserKeyPairContainer) -> PlainFileKey:
    """ decrypt a file key with given plain user keypair """

    logger.info("Decrypting file key: %s", keypair.privateKeyContainer.version)

    key = base64.b64decode(file_key.key)
    private_key_pem = keypair.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(
        data=private_key_pem.encode('ascii'), password=None)

    file_key_version = get_file_key_version(keypair)

    plain_key = None

    if keypair.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value:
        plain_key = private_key.decrypt(ciphertext=key, padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                  algorithm=hashes.SHA1(),
                                                                                  label=None))
    # use SHA256 (hash and MGF1)
    elif keypair.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value:
        plain_key = private_key.decrypt(ciphertext=key, padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),
                                                                                  algorithm=hashes.SHA256(),
                                                                                  label=None))

    if plain_key != None:
        return PlainFileKey(**{
            "version": PlainFileKeyVersion.AES256GCM.value,
            "key": base64.b64encode(plain_key).decode('ascii'),
            "iv": file_key.iv,
            "tag": file_key.tag
        })
    else:
        raise FileKeyEncryptionError(message='Could not encrypt file key')


def decrypt_bytes(enc_data: bytes, plain_file_key: PlainFileKey) -> bytes:
    """ decrypt bytes with given plain file key (on the fly) """
    logger.info("Decrypting bytes with version: %s", plain_file_key.version)

    if enc_data == None:
        raise CryptoMissingDataError(message='No data to process.')

    key = base64.b64decode(plain_file_key.key)
    iv = base64.b64decode(plain_file_key.iv)
    tag = base64.b64decode(plain_file_key.tag)

    decryptor = Cipher(algorithm=algorithms.AES(
        key), mode=modes.GCM(iv, tag)).decryptor()

    plain_bytes = decryptor.update(data=enc_data) + decryptor.finalize()

    return plain_bytes


def encrypt_bytes(plain_data: bytes, plain_file_key: PlainFileKey) -> Tuple[bytes, PlainFileKey]:
    """ encrypt bytes with given plain file key (on the fly) """
    logger.info("Encrypting bytes with version: %s", plain_file_key.version)

    if not bytes:
        raise CryptoMissingDataError(message='No data to process.')

    key = base64.b64decode(plain_file_key.key)
    iv = base64.b64decode(plain_file_key.iv)

    encryptor = Cipher(algorithm=algorithms.AES(key),
                       mode=modes.GCM(iv)).encryptor()
    enc_bytes = encryptor.update(plain_data) + encryptor.finalize()

    plain_file_key.tag = base64.b64encode(encryptor.tag).decode('ascii')

    return (enc_bytes, plain_file_key)


class FileEncryptionCipher:
    """
    Instantiates an encryption cipher
    To be used for chunking
    Initialized with plain file key

    Usage: 
    cipher = FileEncryptionCipher(plain_file_key)

    with open(some_file, 'rb') as plain_file:
        while True:
            chunk = plain_file.read(CHUNK_SIZE)
            if not chunk: break

            cipher.encode_bytes(chunk)

        enc_bytes, plain_file_key = cipher.finalize()

    """

    def __init__(self, plain_file_key: PlainFileKey):
        """ initialize encryptor with a plain file key """
        
        if not plain_file_key.version or not plain_file_key.key or not plain_file_key.iv:
            logger.critical("Invalid file key format (lack of iv or key).")
            raise InvalidFileKeyError(message="Invalid file key")
        if plain_file_key.version != PlainFileKeyVersion.AES256GCM.value and plain_file_key.version != PlainFileKeyVersion.AES256GCM.value:
            logger.critical("Invalid / unknown file key version.")
            raise InvalidFileKeyError(message="Invalid file key version")
        
        logger.info("Initialized encryptor with version: %s", plain_file_key.version)

        self.plain_file_key = plain_file_key

        self.key = base64.b64decode(plain_file_key.key)
        self.iv = base64.b64decode(plain_file_key.iv)

        self.encryptor = Cipher(algorithm=algorithms.AES(
            self.key), mode=modes.GCM(self.iv)).encryptor()

    def encode_bytes(self, plain_data: bytes) -> bytes:
        """ encode bytes """
        logger.debug("Encrypting bytes...")
        return self.encryptor.update(plain_data)

    def finalize(self) -> Tuple[bytes, PlainFileKey]:
        """ complete encryption """
        logger.debug("Finalizing encryption...")
        enc_bytes = self.encryptor.finalize()
        self.plain_file_key.tag = base64.b64encode(
            self.encryptor.tag).decode('ascii')

        return enc_bytes, self.plain_file_key


class FileDecryptionCipher:
    """
    Instantiates a decryption cipher
    To be used for chunking
    Initialized with plain file key

    Usage: 
    cipher = FileDecryptionCipher(plain_file_key)

    with open(some_file, 'rb') as encoded_file:
        while True:
            chunk = encoded_file.read(CHUNK_SIZE)
            if not chunk: break

            cipher.decode_bytes(chunk)

        plain_bytes = cipher.finalize()

    """

    def __init__(self, plain_file_key: PlainFileKey):
        """ initialize decryptor with a plain file key """
        if not plain_file_key.version or not plain_file_key.key or not plain_file_key.iv:
            logger.critical("Invalid file key format (lack of iv or key).")
            raise InvalidFileKeyError(message="Invalid file key")
        if plain_file_key.version != PlainFileKeyVersion.AES256GCM.value and plain_file_key.version != PlainFileKeyVersion.AES256GCM.value:
            logger.critical("Invalid / unknown file key version.")
            raise InvalidFileKeyError(message="Invalid file key version")
        self.plain_file_key = plain_file_key

        self.key = base64.b64decode(plain_file_key.key)
        self.iv = base64.b64decode(plain_file_key.iv)
        self.tag = base64.b64decode(plain_file_key.tag)

        self.encryptor = Cipher(algorithm=algorithms.AES(
            self.key), mode=modes.GCM(self.iv, self.tag)).decryptor()

        logger.info("Initialized encryptor with version: %s", plain_file_key.version)

    def decode_bytes(self, enc_data: bytes) -> bytes:
        """ decode bytes """
        logger.debug("Decrypting bytes...")
        return self.encryptor.update(enc_data)

    def finalize(self) -> bytes:
        """ complete decryption """
        logger.debug("Finalizing encryption...")
        plain_bytes = self.encryptor.finalize()

        return plain_bytes
