
from dracoon.public import DRACOONPublic
from dracoon import DRACOONClient, OAuth2ConnectionType
import dotenv
import os
import asyncio

from dracoon.public.responses import AuthADInfoList, AuthOIDCInfoList, SystemInfo

dotenv.load_dotenv()

client_id = os.environ.get('CLIENT_ID')
client_secret = os.environ.get('CLIENT_SECRET')
username = os.environ.get('E2E_USER_NAME')
password = os.environ.get('E2E_PASSWORD')
base_url = os.environ.get('E2E_BASE_URL')

async def test_settings_e2e():

    dracoon = DRACOONClient(base_url=base_url, client_id=client_id, client_secret=client_secret)
    await dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
    public = DRACOONPublic(dracoon_client=dracoon)
    assert isinstance(public, DRACOONPublic)
    print('Connection test complete (/)')

    system_info = await public.get_system_info()
    assert isinstance(system_info, SystemInfo)
    print('Getting system info test passed (/)')

    auth_ad_info = await public.get_auth_ad_info()
    assert isinstance(auth_ad_info, AuthADInfoList)
    print('Getting AD auth info test passed (/)')

    auth_oidc_info = await public.get_auth_openid_info()
    assert isinstance(auth_oidc_info, AuthOIDCInfoList)
    print('Getting OIDC auth info test passed (/)')

    print('Public E2E tests passed (/)')

if __name__ == '__main__':
    asyncio.run(test_settings_e2e())

    

   


