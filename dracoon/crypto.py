# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls keypair generation and file 
# key generation / file encryption
# Version 0.1.0
# Author: Octavio Simone, 09.05.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

from pydantic import validate_arguments
from Crypto.PublicKey import RSA
from .crypto_models import FileKey, PlainUserKeyPairContainer, UserKeyPairContainer, UserKeyPairVersion

# encrypt a private key (requires a plain user keypair container)
@validate_arguments
def encrypt_private_key(secret: str, plainKey: PlainUserKeyPairContainer) -> UserKeyPairContainer:

    private_keyPEM = plainKey.privateKeyContainer.privateKey
    private_key = RSA.import_key(private_keyPEM)

    private_key_encrypted = private_key.export_key('PEM', secret, pkcs=8, protection='PBKDF2WithHMAC-SHA1AndAES256-CBC')

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


def create_file_key() -> FileKey:
    ...

def encrypt_file(fileKey: FileKey, file):
    ...

