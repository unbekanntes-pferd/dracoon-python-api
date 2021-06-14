# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls keypair generation and file 
# key generation / file encryption
# Version 0.1.0
# Author: Octavio Simone, 12.06.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#

from typing import Tuple
from pydantic import validate_arguments
from .crypto_models import FileKey, FileKeyVersion, PlainFileKey, PlainFileKeyVersion, PlainUserKeyPairContainer, PrivateKeyContainer, PublicKeyContainer, UserKeyPairContainer, UserKeyPairVersion
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.ciphers import (Cipher, algorithms, modes)
import os
import base64

# encrypt a private key (requires a plain user keypair container)
@validate_arguments
def encrypt_private_key(secret: str, plain_key: PlainUserKeyPairContainer) -> UserKeyPairContainer:
    
    # load plain private key 
    private_key_pem = plain_key.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(data=private_key_pem.encode('ascii'), password=None)

    # serialize key with passphrase (secret)
    encrypted_private_key = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                   format=serialization.PrivateFormat.PKCS8,
                                   encryption_algorithm=serialization.BestAvailableEncryption(secret.encode('ascii')))

    return {
       
       "privateKeyContainer": {
           "version": plain_key.privateKeyContainer.version.value,
           "privateKey": encrypted_private_key.decode('ascii') 
       },
       "publicKeyContainer": {
           "version": plain_key.publicKeyContainer.version.value,
           "publicKey": plain_key.publicKeyContainer.publicKey
       } 
   }

# decrypt a private key (requires an encrypted user keypair container)
@validate_arguments
def decrypt_private_key(secret: str, keypair: UserKeyPairContainer) -> PlainUserKeyPairContainer:

    # load encrypted private key 
    private_key_pem = keypair.privateKeyContainer.privateKey
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(data=private_key_pem.encode('ascii'), password=secret.encode('ascii'), )

    # export without passphrase
    private_key_pem = private_key.private_bytes(encoding=serialization.Encoding.PEM,
                                   format=serialization.PrivateFormat.TraditionalOpenSSL,
                                   encryption_algorithm=serialization.NoEncryption())

    return {
       
       "privateKeyContainer": {
           "version": keypair.privateKeyContainer.version.value,
           "privateKey": private_key_pem.decode('ascii')    
       },
       "publicKeyContainer": {
           "version": keypair.publicKeyContainer.version.value,
           "publicKey": keypair.publicKeyContainer.publicKey
       } 
   }

# create a plain user keypair (needs to be encrypted)
@validate_arguments
def create_plain_userkeypair(version: UserKeyPairVersion) -> PlainUserKeyPairContainer:
   
   # generate asymmetric RSA key based on version
   if version == UserKeyPairVersion.RSA2048:
       key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
   elif version == UserKeyPairVersion.RSA4096:
       key = rsa.generate_private_key(public_exponent=65537, key_size=4096)
   else:
    raise ValueError('Invalid keypair version')
   
   private_key_pem = key.private_bytes(encoding=serialization.Encoding.PEM,
                                   format=serialization.PrivateFormat.TraditionalOpenSSL,
                                   encryption_algorithm=serialization.NoEncryption())
   public_key = key.public_key()
   public_key_pem = public_key.public_bytes(encoding=serialization.Encoding.PEM, format=serialization.PublicFormat.SubjectPublicKeyInfo)


   return {
       
       "privateKeyContainer": {
           "version": version.value,
           "privateKey": private_key_pem.decode('ascii')    
       },
       "publicKeyContainer": {
           "version": version.value,
           "publicKey": public_key_pem.decode('ascii')   
       } 
   }

# get correct file key version using a keypair
def get_file_key_version(keypair: UserKeyPairContainer) -> FileKeyVersion:
    if keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value and keypair["privateKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value:
        return FileKeyVersion.RSA2048_AES256GCM
    elif keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value and keypair["privateKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value:
        return FileKeyVersion.RSA_4096_AES256GCM
    else:
        raise ValueError('Invalid user keypair version')

# get correct file key version using a public key
def get_file_key_version_public(public_key: PublicKeyContainer) -> FileKeyVersion:
    if public_key["version"] == UserKeyPairVersion.RSA2048.value:
        return FileKeyVersion.RSA2048_AES256GCM
    elif public_key["version"] == UserKeyPairVersion.RSA4096.value:
        return FileKeyVersion.RSA_4096_AES256GCM
    else:
        raise ValueError('Invalid user keypair version')

# create a plain file key
@validate_arguments
def create_file_key(version: FileKeyVersion) -> PlainFileKey:

    # get random bytes for key and vector
    key = os.urandom(32)
    iv = os.urandom(12)

    # base64 encode both strings
    encoded_key = base64.b64encode(key)
    encoded_iv = base64.b64encode(iv)

    return {
        "version": version.value,
        "key": encoded_key.decode('ascii'),
        "iv": encoded_iv.decode('ascii'),
        "tag": None
    }

def encrypt_file_key_public(plain_file_key: PlainFileKey, public_key: PublicKeyContainer):
    public_key_pem = serialization.load_pem_public_key(public_key["publicKey"].encode('ascii'))
    # check correct version
    file_key_version = get_file_key_version_public(public_key)

    key = plain_file_key["key"]
    
    # initialize variable for encrypted file key
    encrypted_key = None

    # use SHA1 MGF1 and SHA256 hash
    if public_key["version"] == UserKeyPairVersion.RSA2048.value:
        encrypted_key = public_key_pem.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA1(),
                                       label=None))
    # use SHA256 (hash and MGF1)
    elif public_key["version"] == UserKeyPairVersion.RSA4096.value:
        encrypted_key = public_key_pem.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA256(),
                                       label=None))
    return {
        "version": file_key_version.value,
        "key": base64.b64encode(encrypted_key).decode(),
        "iv": plain_file_key["iv"],
        "tag": plain_file_key["tag"]
    }

# encrypt a plain file key
def encrypt_file_key(plain_file_key: PlainFileKey, keypair: PlainUserKeyPairContainer) -> FileKey:

    private_key_pem = keypair["privateKeyContainer"]["privateKey"]
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(data=private_key_pem.encode('ascii'), password=None)
    public_key = private_key.public_key()

    # check correct version
    file_key_version = get_file_key_version(keypair)

    key = plain_file_key["key"]
    
    # initialize variable for encrypted file key
    encrypted_key = None

    # use SHA1 MGF1 and SHA256 hash
    if keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value:
        encrypted_key = public_key.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA1(),
                                       label=None))
    # use SHA256 (hash and MGF1)
    elif keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value:
        encrypted_key = public_key.encrypt(plaintext=base64.b64decode(key), padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA256(),
                                       label=None))
    return {
        "version": file_key_version.value,
        "key": base64.b64encode(encrypted_key).decode(),
        "iv": plain_file_key["iv"],
        "tag": plain_file_key["tag"]
    }

def decrypt_file_key(fileKey: FileKey, keypair: PlainUserKeyPairContainer) -> PlainFileKey:
    
    file_key = base64.b64decode(fileKey["key"])
    private_key_pem = keypair["privateKeyContainer"]["privateKey"]
    private_key: rsa.RSAPrivateKeyWithSerialization = serialization.load_pem_private_key(data=private_key_pem.encode('ascii'), password=None)

    file_key_version = get_file_key_version(keypair)

    plain_key = None

    if keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA2048.value:
        plain_key = private_key.decrypt(ciphertext=file_key, padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA1(),
                                       label=None))
    # use SHA256 (hash and MGF1)
    elif keypair["publicKeyContainer"]["version"] == UserKeyPairVersion.RSA4096.value:
        plain_key = private_key.decrypt(ciphertext=file_key, padding=padding.OAEP(mgf=padding.MGF1(algorithm=hashes.SHA256()),    
                                       algorithm=hashes.SHA256(),
                                       label=None))
        
    
    if plain_key != None:
        return {
        "version": fileKey["version"],
        "key": base64.b64encode(plain_key).decode('ascii'),
        "iv": fileKey["iv"],
        "tag": fileKey["tag"]
    }
    else: 
        raise ValueError('Could not encrypt file key.')


def decrypt_bytes(enc_data: bytes, plain_file_key: PlainFileKey) -> bytes:
    if enc_data == None:
        raise ValueError('No data to process.')

    
    key = base64.b64decode(plain_file_key["key"])
    iv = base64.b64decode(plain_file_key["iv"])
    tag = base64.b64decode(plain_file_key["tag"])

    decryptor = Cipher(algorithm=algorithms.AES(key), mode=modes.GCM(iv, tag)).decryptor()

    plain_bytes = decryptor.update(data=enc_data) + decryptor.finalize() 

    return plain_bytes


def encrypt_bytes(plain_data: bytes, plain_file_key: PlainFileKey) -> Tuple[bytes, PlainFileKey]:
    if not bytes:
        raise ValueError('No data to process.')

    key = base64.b64decode(plain_file_key["key"])
    iv = base64.b64decode(plain_file_key["iv"])

    encryptor = Cipher(algorithm=algorithms.AES(key), mode=modes.GCM(iv)).encryptor()
    enc_bytes = encryptor.update(plain_data) + encryptor.finalize()

    plain_file_key["tag"] = base64.b64encode(encryptor.tag).decode('ascii')

    return (enc_bytes, plain_file_key)
    