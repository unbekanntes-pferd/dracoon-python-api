# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls keypair generation and file 
# key generation / file encryption
# Version 0.1.0
# Author: Octavio Simone, 09.05.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

from pydantic import validate_arguments
from Crypto.PublicKey import RSA
from Crypto.Random import get_random_bytes
from .crypto_models import FileKey, FileKeyVersion, PlainFileKey, PlainFileKeyVersion, PlainUserKeyPairContainer, UserKeyPairContainer, UserKeyPairVersion
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Hash import SHA256, SHA1
from Crypto.Signature import pss
import base64

# encrypt a private key (requires a plain user keypair container)
@validate_arguments
def encrypt_private_key(secret: str, plainKey: PlainUserKeyPairContainer) -> UserKeyPairContainer:

    private_keyPEM = plainKey.privateKeyContainer.privateKey
    private_key = RSA.import_key(private_keyPEM)

    private_key_encrypted = private_key.export_key('PEM', secret, protection='PBKDF2WithHMAC-SHA1AndAES256-CBC')

    return {
       
       "privateKeyContainer": {
           "version": plainKey.privateKeyContainer.version.value,
           "privateKey": private_key_encrypted.decode('ascii') 
       },
       "publicKeyContainer": {
           "version": plainKey.publicKeyContainer.version.value,
           "publicKey": plainKey.publicKeyContainer.publicKey
       } 
   }

# decrypt a private key (requires an encrypted user keypair container)
@validate_arguments
def decrypt_private_key(secret: str, keypair: UserKeyPairContainer):

    plain_keypair = RSA.import_key(keypair.privateKeyContainer.privateKey, secret)

    private_key = plain_keypair.export_key('PEM')

    return {
       
       "privateKeyContainer": {
           "version": keypair.privateKeyContainer.version.value,
           "privateKey": private_key.decode('ascii')    
       },
       "publicKeyContainer": {
           "version": keypair.publicKeyContainer.version.value,
           "publicKey": keypair.publicKeyContainer.publicKey
       } 
   }

# create a plain user keypair (needs to be encrypted)
@validate_arguments
def create_plain_userkeypair(version: UserKeyPairVersion) -> PlainUserKeyPairContainer:
   if version == UserKeyPairVersion.RSA2048:
       key: RSA.RsaKey = RSA.generate(bits=2048, e=65537)
   elif version == UserKeyPairVersion.RSA4096:
       key: RSA.RsaKey = RSA.generate(bits=4096, e=65537)
   else:
    raise ValueError('Invalid keypair version')

   private_key = key.export_key('PEM')
   public_key = key.publickey().export_key('PEM')

   return {
       
       "privateKeyContainer": {
           "version": version.value,
           "privateKey": private_key.decode('ascii')    
       },
       "publicKeyContainer": {
           "version": version.value,
           "publicKey": public_key.decode('ascii')   
       } 
   }

def get_file_key_version(keypair: UserKeyPairContainer) -> FileKeyVersion:
    if keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value and keypair["privateKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value:
        return FileKeyVersion.RSA2048_AES256GCM
    elif keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value and keypair["privateKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value:
        return FileKeyVersion.RSA_4096_AES256GCM
    else:
        raise ValueError('Invalid user keypair version')

# create a plain file key
@validate_arguments
def create_file_key(version: PlainFileKeyVersion) -> PlainFileKey:

    # get random bytes for key and vector
    key = get_random_bytes(32)
    iv = get_random_bytes(12)

    # base64 encode both strings
    encoded_key = base64.b64encode(key)
    encoded_iv = base64.b64encode(iv)

    return {
        "version": version.value,
        "key": encoded_key.decode('ascii'),
        "iv": encoded_iv.decode('ascii'),
        "tag": None
    }

# encrypt a plain file key
def encrypt_file_key(plain_fileKey: PlainFileKey, keypair: UserKeyPairContainer) -> FileKey:
    
    # import public key PEM
    public_key = RSA.import_key(keypair["publicKeyContainer"]["publicKey"])
    # check correct version
    file_key_version = get_file_key_version(keypair)

    cipher = None
    
    # use SHA1 MGF1 and SHA256 hash
    if keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value:
        cipher = PKCS1_OAEP.new(key=public_key, hashAlgo=SHA256, mgfunc= lambda x, y: pss.MGF1(x, y, SHA1))

    # use SHA256 (hash and MGF1)
    elif keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value:
        cipher = PKCS1_OAEP.new(key=public_key, hashAlgo=SHA256)

    return {
        "version": file_key_version.value,
        "key": (base64.b64encode(cipher.encrypt(str.encode(plain_fileKey["key"])))).decode(),
        "iv": (plain_fileKey["iv"]),
        "tag": None
    }



    
