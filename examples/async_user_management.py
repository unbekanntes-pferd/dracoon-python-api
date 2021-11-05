"""
Example script showing the new async API and user management possibilities

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    await dracoon.connect()


    """ create some user payload """
    local_user = dracoon.users.make_local_user('TEST', 'TEST', 'xxx@xxx.com', 'testdc1')
    oidc_user = dracoon.users.make_oidc_user('TEST', 'TEST', 'xxx@xxx.com', 'testdc2', 5)
    ad_user = dracoon.users.make_ad_user('TEST', 'TEST', 'xxx@xxx.com', 'testdc3', 4)
    
    """ send requests """
    local_res = await dracoon.users.create_user(local_user)
    ad_res = await dracoon.users.create_user(ad_user)
    oidc_res = await dracoon.users.create_user(oidc_user)

    """ fetch ids """
    ad_id = ad_res.json()["id"]
    oidc_id = oidc_res.json()["id"]
    local_id = local_res.json()["id"]

    """ delete just created users by id """
    await dracoon.users.delete_user(local_id)
    await dracoon.users.delete_user(oidc_id)
    await dracoon.users.delete_user(ad_id)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())