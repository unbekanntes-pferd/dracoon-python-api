"""
Export user list to CSV file

12.01.2024 Octavio Simone
"""

import asyncio
import csv

from dracoon import DRACOON
from dracoon.client import OAuth2ConnectionType


base_url = 'https://staging.dracoon.com'

# set up client with client credentials
# redirect uri must be set to https://your.domain.com/oauth/callback
client_id = 'XXXXXXXXXXX' 
client_id = 'XXXXXXXXXXX' 

username = 'XXXXXXXXXXX' # replace with username
password = 'XXXXXXXXXXX' # replace with password / getpass.getpass to enter password


async def main():
    dracoon = DRACOON(base_url=base_url, client_id=client_id,
                      raise_on_err=True, log_file_out=False, log_stream=True)
    
    print("Please log in using the following link: ")
    print(dracoon.get_code_url())

    auth_code = input("Enter auth code: ")
    
    await dracoon.connect(connection_type=OAuth2ConnectionType.auth_code, auth_code=auth_code)

    user_list = await dracoon.users.get_users()

    if user_list.range.total > 500:
        user_reqs = [dracoon.users.get_users(offset=offset) for offset in range(0, user_list.range.total, 500)]

        for batch in dracoon.batch_process(user_reqs):
            next_lists = asyncio.gather(*batch)

            for next_list in next_lists:
                user_list.items.extend(next_list.items)
    
    dracoon.logger.info((f"Found {len(user_list.items)} users"))

    with open('users.csv', 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

        writer.writerow(['id', 'username', 'first_name', 'last_name', 'email', 'created_at', 'last_login_at'])

        for user in user_list.items:
            last_login = user.lastLoginSuccessAt if user.lastLoginSuccessAt else "N/A"
            writer.writerow([user.id, user.userName, user.firstName, user.lastName, user.email, user.createdAt, last_login])


if __name__ == '__main__':
    asyncio.run(main())
