"""
Example script showing the new async API with keypair reset (delete old keypair, set new one)

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON
from dracoon.crypto_models import UserKeyPairVersion
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    connection = await dracoon.connect()
    print(dracoon.client.connected)

    res = await dracoon.user.delete_user_keypair()

    print(res)

    secret = 'VerySecret123!' # replace with own secret 

    res = await dracoon.user.set_user_keypair(secret)
    
    """
    You can explicitly set a version using: 
    res = await account.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096) 
    res = await account.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
    """

    print(res)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())