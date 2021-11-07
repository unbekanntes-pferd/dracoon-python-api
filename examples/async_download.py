"""
Example script showing the new async API with full chunked & encrypted download support

06.11.2021 Octavio Simone

"""

from dracoon import DRACOON

import asyncio

baseURL = 'https://dracoon.team'
client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

async def main():

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)

    secret ='VerySecret1234!' # use getpass to prompt for decryption password

    await dracoon.get_keypair(secret)

    target = '/Users/some/test/path'

    source = '/Crypto/Unbenannt.jpeg'
    source1 = '/Crypto/verylarge50MB.pdf'
    source2 = '/Crypto/1GB.bin'
    source3 = '/DEMO/ubpf.png'

    files = [source, source1, source2, source3]

    for file in files:
        await dracoon.download(file_path=file, target_path=target)

    await dracoon.logout()
if __name__ == '__main__':
    asyncio.run(main())
