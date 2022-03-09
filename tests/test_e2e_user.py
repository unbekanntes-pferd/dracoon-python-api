
from dracoon.crypto.models import UserKeyPairContainer, UserKeyPairVersion
from dracoon.user import DRACOONUser
from dracoon import DRACOONClient, OAuth2ConnectionType
import dotenv
import os
import asyncio

from dracoon.user.models import UpdateAccount, UserAccount


dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

async def test_user_e2e():

    dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    user = DRACOONUser(dracoon_client=dracoon)
    assert isinstance(user, DRACOONUser)
    print('Connection test complete (/)')
        
    user_info = await user.get_account_information(more_info=True)
    assert isinstance(user_info, UserAccount)
    print('Getting user info passed (/)')

    account_update = user.make_account_update(phone='999999999')
    assert isinstance(account_update, UpdateAccount)
    print('Making account update payload test passed (/)')

    account_update_res = await user.update_account_information(account_update=account_update)

    assert account_update_res.phone == '999999999'
    print('Updating user account test passed (/)')

    secret = 'VerySecret123!'

    keypair_2048 = await user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA2048)
    assert keypair_2048 == None

    print('Setting keypair RSA 2048 passed (/)')

    keypair_2048 = await user.get_user_keypair()

    assert isinstance(keypair_2048, UserKeyPairContainer)
    assert keypair_2048.privateKeyContainer.version == UserKeyPairVersion.RSA2048.value
    assert keypair_2048.publicKeyContainer.version == UserKeyPairVersion.RSA2048.value

    print('Getting keypair RSA 2048 passed (/)')

    del_keypair = await user.delete_user_keypair(version=UserKeyPairVersion.RSA2048)
    assert del_keypair == None

    print('Deleting keypair test passed (/)')

    keypair_4096 = await user.set_user_keypair(secret=secret, version=UserKeyPairVersion.RSA4096)
    assert keypair_4096 == None

    print('Setting keypair RSA 4096 passed (/)')

    keypair_4096 = await user.get_user_keypair()

    assert isinstance(keypair_4096, UserKeyPairContainer)
    assert keypair_4096.privateKeyContainer.version == UserKeyPairVersion.RSA4096.value
    assert keypair_4096.publicKeyContainer.version == UserKeyPairVersion.RSA4096.value

    print('Getting keypair RSA 4096 passed (/)')

    del_keypair = await user.delete_user_keypair(version=UserKeyPairVersion.RSA4096)
    assert del_keypair == None

    print('User E2E tests passed (/)')

if __name__ == '__main__':
    asyncio.run(test_user_e2e())

    

   


