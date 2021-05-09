# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls keypair generation and file 
# key generation / file encryption
# Version 0.1.0
# Author: Octavio Simone, 09.05.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

from Crypto.PublicKey import RSA
from .crypto_models import FileKey, PlainUserKeyPairContainer, UserKeyPairContainer, UserKeyPairVersion

def encryptPrivateKey(secret: str, plainKey: PlainUserKeyPairContainer) -> UserKeyPairContainer:
    ...

def decryptPrivateKey(secret: str, keypair: UserKeyPairContainer):
    ...

def createPlainUserKeyPair(version: UserKeyPairVersion) -> PlainUserKeyPairContainer:
   if version == UserKeyPairVersion.RSA2048:
       key: RSA.RsaKey = RSA.generate(bits=2048, e=65537)
   elif version == UserKeyPairVersion.RSA4096:
       key: RSA.RsaKey = RSA.generate(bits=4096, e=65537)
   else:
    raise ValueError('Invalid keypair version')

   private_key = key.export_key(pkcs=8)
   public_key = key.publickey().export_key()

   return {
       "privateKeyContainer": private_key.decode('ascii'),
       "publicKeyContainer": public_key.decode('ascii')
   }


def createFileKey() -> FileKey:
    ...

def encryptFile(fileKey: FileKey, file):
    ...

