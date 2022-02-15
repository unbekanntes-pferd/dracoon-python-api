
"""
Update all users of a certain domain to openID
15.02.22 Quirin Wierer
"""

from os import system
from dracoon import DRACOON, user
import asyncio

from dracoon.nodes_models import ProcessRoomPendingUsers, UpdateRoomGroups
from dracoon.nodes_responses import RoomGroup
from dracoon.user_responses import UserItem
 
async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXX'
    client_secret = 'XXXXXXXX'

    #domain filter
    filter = 'userName:cn:@domain.com'
    #OpenID config ID
    oidc_id = 1

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)
    
    user_list = []

    # retrieve users (of given domain)
    users = await dracoon.users.get_users(offset=0, filter = filter)
    user_list = [*users.items]
    if users.range.total > 500:
        for offset in range(500,users.range.total,500):
            userlist = await dracoon.users.get_users(offset=offset, filter = filter)
            user_list = [*userlist.items]
            
    #change auth method
    for user in user_list:
        auth_data = dracoon.users.make_auth_data(method="openid", oidc_id=oidc_id, login=user.email)
        payload = dracoon.users.make_user_update(auth_data=auth_data)
        await dracoon.users.update_user(user_id=user.id, user_update=payload)

    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())