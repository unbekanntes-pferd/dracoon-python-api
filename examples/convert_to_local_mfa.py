"""
Script to convert all OIDC users to local users and activate MFA

Usage: 
- set OIDC config id
- verify params (username = username used in OIDC IdP)
- run script

16.11.2022 Octavio Simone
"""


import sys

import asyncio

from typing import Any, Coroutine, List

from dracoon import DRACOON
from dracoon.client import OAuth2ConnectionType
from dracoon.errors import DRACOONHttpError, HTTPForbiddenError, HTTPUnauthorizedError
from dracoon.user.responses import UserData, UserList

base_url = 'https://demo.dracoon.com'
client_id = 'XXXXXXXXXXXXXXXXXXXXXXXX' 
client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXX'

username = 'XXXXXXXXXXXXXXXXXXXXXXXX' # replace with username
password = 'XXXXXXXXXXXXXXXXXXXXXXXX' # replace with password / getpass.getpass to enter password

OIDC_CONFIG_ID = 99 # replace with config
OIDC_NAME = 'DRACOON' # replace with OIDC config name

class DCUserConverter:
    def __init__(self, dracoon_url: str):
        self.dracoon = DRACOON(base_url=dracoon_url, client_id=client_id, client_secret=client_secret, 
                               raise_on_err=True, log_file_out=True)
    

    def create_get_user_req(self, user_id: int) -> Coroutine[Any, Any, UserData]:
        return self.dracoon.users.get_user(user_id=user_id)

    async def get_user_data(self, user_ids: List[int]) -> List[UserData]:
        
        user_data_list = []
        user_reqs = [self.create_get_user_req(user_id=user_id) for user_id in user_ids]
        
        for batch in self.dracoon.batch_process(coro_list=user_reqs, batch_size=10):
            user_data_resps: List[UserData] = await asyncio.gather(*batch)
            user_data_list.extend(user_data_resps)
        
        return user_data_list

    def filter_user_data_list(self, user_list: List[UserData], oidc_id: int, test_run: bool = False) -> List[UserData]:
        """ filter """
        
        filtered_list = [user for user in user_list 
                            if user.authData.method == 'openid' and user.authData.oidConfigId == oidc_id]
        
        if test_run:
            filtered_list = [user for user in user_list 
                            if user.authData.method == 'openid' and user.authData.oidConfigId == oidc_id 
                            and user.authData.login.startswith('test_user_')]
        
        return filtered_list
        
    async def get_users(self) -> UserList:
        """ get user list """
        try:
            user_list = await self.dracoon.users.get_users()
        except HTTPForbiddenError:
            await self.graceful_exit()
            self.dracoon.logger.critical("Insufficient permissions (user manager).")
            sys.exit(1)
        except DRACOONHttpError:
            await self.graceful_exit()
            self.dracoon.logger.critical("Error fetching users.")
            sys.exit(1)     
            
        if user_list.range.total > 500:
            user_reqs = [self.dracoon.users.get_users(offset=offset) for offset in range(500, user_list.range.total, 500)]
            
            for batch in self.dracoon.batch_process(coro_list=user_reqs):
                try:
                    user_resp: List[UserList] = await asyncio.gather(*batch)
                    for resp in user_resp:
                        user_list.items.extend(resp.items)
                except DRACOONHttpError:
                    await self.graceful_exit()
                    self.dracoon.logger.critical("Error fetching users.")
                    sys.exit(1)
        
        return user_list
                    

    async def update_user(self, user_data: UserData):
        """ update a user (set username, enforce MFA, auth method local user) """
        local_auth = self.dracoon.users.make_auth_data(method='basic')
        new_user_name = user_data.userName.split('\\')[1]
        user_update = self.dracoon.users.make_user_update(auth_data=local_auth, mfa_enforced=True, user_name=new_user_name)
        
        try:
            await self.dracoon.users.update_user(user_id=user_data.id, user_update=user_update)
            self.dracoon.logger.info("Updated user %s (mfa enforced, new username: %s)", user_data.userName, new_user_name)
        except HTTPForbiddenError:
            await self.graceful_exit()
            self.dracoon.logger.critical("Insufficient permissions (user manager).")
            sys.exit(1)
        except DRACOONHttpError:
            await self.graceful_exit()
            self.dracoon.logger.critical("Error updating user.")
            sys.exit(1)   
    

    async def connect(self, username: str, password: str):
        """ connect to DRACOON via password flow  """
 
        try:
            await self.dracoon.connect(connection_type=OAuth2ConnectionType.password_flow, username=username, password=password)
        except HTTPUnauthorizedError:
            await self.graceful_exit()
            self.dracoon.logger.critical("Wrong credentials.")
            sys.exit(1)
        except DRACOONHttpError:
            await self.graceful_exit()
            self.dracoon.logger.critical("An error ocurred during login.")
            sys.exit(1)
        

    async def graceful_exit(self):
        """ close httpx client on error """
        if self.dracoon.connection:
            await self.dracoon.logout()
        else:
            await self.dracoon.client.disconnect()

    async def delete_user(self, user_id: int):
        """ delete a user """
        await self.dracoon.users.delete_user(user_id=user_id)

    async def seed_users(self, count: int = 200):
        """ create a batch of test users for given OIDC config """
        
        logins = [f"test_user_{num}" for num in range(0, count)]
        user_reqs = [self.create_test_oidc_user(login=login) for login in logins]
        
        for batch in self.dracoon.batch_process(coro_list=user_reqs, batch_size=5):
            try:
                await asyncio.gather(*batch)
            except DRACOONHttpError:
                await self.graceful_exit()
                self.dracoon.logger.critical('Error creating users')
                sys.exit(1)
            
    async def unseed_users(self, name_pattern: str = 'test_user_', auth_method: str = 'basic'):
        """ delete the batch of test users created with seed (WARNING: deletes local accounts for 'test_user_' users """
        user_list = await self.get_users()
        user_ids = [user.id for user in user_list.items]
        user_data_list = await self.get_user_data(user_ids=user_ids)
        filtered_user_data = [user_data for user_data in user_data_list 
                            if user_data.authData.method == auth_method and user_data.userName.startswith(name_pattern)]
        del_reqs = [self.delete_user(user_id=user_data.id) for user_data in filtered_user_data]

        for batch in self.dracoon.batch_process(coro_list=del_reqs, batch_size=5):
            try:
                await asyncio.gather(*batch)
            except DRACOONHttpError:
                await self.graceful_exit()
                self.dracoon.logger.critical('Error creating users')
                sys.exit(1)

    async def create_test_oidc_user(self, login: str):
        """ create oidc user for given OIDC config ID """
        oidc_user = self.dracoon.users.make_oidc_user(first_name='test', last_name='test',
                                                email='foo@dracoon.com', oidc_id=OIDC_CONFIG_ID, login=login)
        
        user = await self.dracoon.users.create_user(user=oidc_user)
        
        return user
    
    async def convert_oidc_users(self, test_run: bool = False):
        """ convert all users of a given OIDC config id to local users with MFA enforced """
        user_list = await self.get_users()
        user_ids = [user.id for user in user_list.items]
        user_data_list = await self.get_user_data(user_ids=user_ids)
        user_data_filtered_list = self.filter_user_data_list(user_list=user_data_list, oidc_id=OIDC_CONFIG_ID, test_run=test_run)
        self.dracoon.logger.info('Identified %s users with OIDC id %s.', len(user_data_filtered_list), OIDC_CONFIG_ID)
        update_user_reqs = [self.update_user(user_data=user_data) for user_data in user_data_filtered_list]
        
        for batch in self.dracoon.batch_process(coro_list=update_user_reqs, batch_size=2):
            await asyncio.gather(*batch)
    
  
    
async def main():
    """ convert users from OIDC to local and enforce MFA """
    # create converter
    converter = DCUserConverter(dracoon_url=base_url)
    # connect via password flow
    await converter.connect(username=username, password=password)
    # convert to local and enforce MFA
    await converter.convert_oidc_users()

async def test_main():
    """ test functionality of OIDC to local conversion & MFA enforcement """
    converter = DCUserConverter(dracoon_url=base_url)
    await converter.connect(username=username, password=password)
    
    # remove users from potentially failed ops
    await converter.unseed_users(auth_method='openid', name_pattern=f"{OIDC_NAME}\\test_user_")
    # create 20 OIDC users
    await converter.seed_users(count=20)
    # convert them to local and enforce MFA
    await converter.convert_oidc_users(test_run=True)
    
    # delete users
    await converter.unseed_users()
    

if __name__ == '__main__':
    asyncio.run(test_main())
