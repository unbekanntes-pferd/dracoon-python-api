"""
Iterate through all users of certain group
13.07.22 Quirin Wierer
"""

from dracoon import DRACOON
import asyncio
 
async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXXXXXXXXXXXXXXXXXX'
    client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXX'

    group_id = 999999999999
    group_filter = "isMember:eq:true"

    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())

    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)



    # retrieve users (of given group)
    group_user_list = []

    group_users = await dracoon.groups.get_group_users(group_id=group_id, filter=group_filter)

    group_user_list = [*group_users.items]
    if group_users.range.total > 500:
        for offset in range(500,group_users.range.total,500):
            group_user_list = await dracoon.users.get_users(offset=offset, filter = filter)
            group_user_list = [*group_user_list.items]
    
    #change auth method
    for user in group_user_list:
        print(user.userInfo.id)
        print(user.userInfo.userName)
    await dracoon.logout()

if __name__ == '__main__':
    asyncio.run(main())
