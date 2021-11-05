"""
Example script showing the new async API with chunked encrypted upload

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON

import asyncio

baseURL = 'https://dracoon.team'
client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

async def main():

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    await dracoon.connect()

    plain_keypair = await dracoon.get_keypair()

    file_path = '/test/testfile_200MB.bin'
    file_name = file_path.split('/')[-1]
    
    upload_channel = dracoon.nodes.make_upload_channel(parent_id=999, name=file_name)

    res = await dracoon.nodes.create_upload_channel(upload_channel=upload_channel)
    channel_res = res.json()

    res = await dracoon.uploads.upload_encrypted(file_path=file_path, target_id=8533, upload_channel=channel_res, plain_keypair=plain_keypair)
    
    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())
