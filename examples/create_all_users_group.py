"""
Add missing users of domain to group
14.06.22 Quirin Wierer
"""


from dracoon import DRACOON
import asyncio

from dracoon.user.responses import UserItem

async def main():
    baseURL = 'https://dracoon.team'
    client_id = 'XXXXXX'
    client_secret = 'XXXXXXXXX'
    GROUP_ID = 999999999999
    user_filter = 'userName:cn:Keycloak'

    #establish connection
    dracoon = DRACOON(base_url=baseURL, client_id=client_id, client_secret=client_secret)
    print(dracoon.get_code_url())
    auth_code = input('Enter auth code:')
    await dracoon.connect(auth_code=auth_code)

    #get all users of group
    group_users = await dracoon.groups.get_group_users(group_id=GROUP_ID, offset=0)
    total_group_users = group_users.range.total
    group_user_list = [GroupUser.userInfo.id for GroupUser in group_users.items]

    if total_group_users > 500:
        for offset in range(500, total_group_users, 500):
            group_users = await dracoon.groups.get_group_users(group_id=GROUP_ID, offset=offset)
            for GroupUser in group_users.items:
                user_p = GroupUser.userInfo.id
                group_user_list.append(user_p)

    print (group_user_list)

    #get all userIDs in a certain domain
    user_res = await dracoon.users.get_users(offset=0, filter=user_filter)
    total_users = user_res.range.total
    user_list = [user.id for user in user_res.items]

    if total_users > 500:
        for offset in range(500, total_users, 500):
            user_res = await dracoon.users.get_users(filter=user_filter, offset=offset)
            for user in user_res.items:
                user_p = user.id
                user_list.append(user_p)

    print (user_list)

    #get missing users
    unassigned_users = set(user_list).difference(set(group_user_list))

    print(unassigned_users)


    #add users to group
    #group = await dracoon.groups.add_group_users(group_id = GROUP_ID, user_list=unassigned_users, raise_on_err=True)

if __name__ == '__main__':
    asyncio.run(main())