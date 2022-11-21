"""
Example script showing the new async API with full chunked & encrypted upload support

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

    plain_keypair = await dracoon.get_keypair(secret) # leave out if unencrypted target parent

    target = '/DEMO/XYZ/' # encrypted nodes supported

    file_small = '/test/test.mov'
    file_medium = '/testfile_10MB.bin'
    file_large = '/testfile_200MB.bin'

    files = [file_small, file_medium, file_large]

    for file in files:
        await dracoon.upload(file_path=file, target_path=target, =True)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())
