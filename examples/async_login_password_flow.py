"""
Example script showing the new async API with password flow login

04.11.2021 Octavio Simone

"""

from dracoon import DRACOON, OAuth2ConnectionType
import asyncio

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)

    username = 'username'
    password = 'topsecret' # use getpass.getpass() in interactive scripts

    connection = await dracoon.connect(OAuth2ConnectionType.password_flow, username, password)
    print(connection) # returns token and validity

    connected = await dracoon.test_connection() # test connection as authenticated user

    print(connected)

    await dracoon.logout() # log out (revoke tokens)


if __name__ == '__main__':
    asyncio.run(main())