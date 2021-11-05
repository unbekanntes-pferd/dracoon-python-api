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

    user = {
            "firstName": 'TEST',
            "lastName": 'TEST',
            "userName": 'xxx@xxx.com',
            "receiverLanguage": "de-DE",
            "email": 'xxx@xxx.com',
            "notifyUser": True,
            "authData": {
                "method": "basic",
                "mustChangePassword": True,
            },
            "isNonmemberViewer": True
        }

    res = await dracoon.users.create_user(user)

    print(res)

    await dracoon.logout()


if __name__ == '__main__':
    asyncio.run(main())