"""
Example script showing the new async API with simple user creation

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    connection = await dracoon.connect()

    user = dracoon.users.make_local_user('TEST', 'TEST', 'pferd@unbekanntespferd.com', 'testdc1')
    
    res = await dracoon.users.create_user(user)

    print(res)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())