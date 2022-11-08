"""
Async DRACOON client based on httpx
V1.2.0

(c) Octavio Simone, November 2021 

The client implements all login and logout procedures and is part of every API adapter.

"""

import base64 
import asyncio
import logging
from enum import Enum
from dataclasses import dataclass
from datetime import datetime

import httpx
from dracoon.client.models import ProxyConfig

from dracoon.errors import (MissingCredentialsError, HTTPBadRequestError, HTTPUnauthorizedError, 
                            HTTPPaymentRequiredError, HTTPForbiddenError, HTTPNotFoundError, HTTPConflictError, HTTPPreconditionsFailedError,
                            HTTPUnknownError)

USER_AGENT = 'dracoon-python-1.8.3'
DEFAULT_TIMEOUT_CONFIG = httpx.Timeout(10, connect=30, read=30)

class OAuth2ConnectionType(Enum):
    """ enum as connection type for DRACOONClient """
    """ supports authorization code flow, password flow and refresh token """
    password_flow = 1
    auth_code = 2
    refresh_token = 3

@dataclass
class DRACOONConnection:
    """ DRACOON connection with tokens and validity """
    connected_at: datetime
    access_token: str
    access_token_validity: int
    refresh_token: str

class DRACOONClient:
    """ DRACOON client with an httpx async client """
    """ requires OAuth connection details and base url """
    api_base_url = '/api/v4'
    branding_base_url = '/branding/api'
    reporting_base_url = '/reporting/api'
    headers = {
        "User-Agent": USER_AGENT

    }

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = '', redirect_uri: str = None,
                 raise_on_err: bool = False, proxy_config: ProxyConfig = None):
        """ client is initialized with DRACOON instance details (url and OAuth client credentials) """
        
        # custom transport for retries on connection errors
        DEFAULT_HTTPX_TRANSPORT = httpx.AsyncHTTPTransport(retries=5)
        
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.http = httpx.AsyncClient(headers=self.headers, timeout=DEFAULT_TIMEOUT_CONFIG, proxies=proxy_config, transport=DEFAULT_HTTPX_TRANSPORT)
        self.uploader = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_CONFIG, proxies=proxy_config, transport=DEFAULT_HTTPX_TRANSPORT)
        self.downloader = httpx.AsyncClient(timeout=DEFAULT_TIMEOUT_CONFIG, proxies=proxy_config, transport=DEFAULT_HTTPX_TRANSPORT)
        self.connected = False
        if redirect_uri:
            self.redirect_uri = redirect_uri
        else:
            self.redirect_uri = f"{self.base_url}/oauth/callback"
        self.connection: DRACOONConnection = None
        self.raise_on_err = raise_on_err
        self.logger = logging.getLogger('dracoon.client')
        self.logger.info("DRACOON client created.")
        self.logger.debug(f"DRACOON client config: {self.base_url} // {self.client_id}")

    def __del__(self):
        """ on client destroy terminate async clients """

        # handle asyncio runtime
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        
        # close httpx clients
        if loop and loop.is_running():
            loop.create_task(self.http.aclose())
            loop.create_task(self.uploader.aclose())
            loop.create_task(self.downloader.aclose())
        elif loop and not loop.is_running():
            loop.run_until_complete(self.http.aclose())
            loop.run_until_complete(self.downloader.aclose())
            loop.run_until_complete(self.uploader.aclose())
            

   
    async def connect(self, connection_type: OAuth2ConnectionType, username: str = None, password: str = None, 
                      auth_code: str = None, refresh_token: str = None, redirect_uri: str = None) -> DRACOONConnection:
        """ connects based on given OAuth2ConnectionType """
        token_url = self.base_url + '/oauth/token'
        now = datetime.now()

        self.logger.debug("Establishing DRACOON connection...")
        
        # handle missing credentials for password flow
        if connection_type == OAuth2ConnectionType.password_flow and username == None and password == None:
            await self.http.aclose()
            self.logger.error("Missing credentials for OAuth2 password flow.")
            raise MissingCredentialsError(message='Username and password are mandatory for OAuth2 password flow.')

        # handle missing auth code for authorization code flow 
        if connection_type == OAuth2ConnectionType.auth_code and auth_code == None:
            await self.http.aclose()
            self.logger.error("Missing auth code for OAuth2 password flow.")
            raise MissingCredentialsError(message='Auth code is mandatory for OAuth2 authorization code flow.')
                
        # get connection via OAuth2 password flow
        if connection_type == OAuth2ConnectionType.password_flow:
            data = {'grant_type': 'password',
                'username': username, 'password': password}
            
            token_payload = base64.b64encode(
                bytes(self.client_id + ':' + self.client_secret, 'ascii'))

            self.http.headers["Authorization"] = "Basic " + \
                    token_payload.decode('ascii')
            try:
                res = await self.http.post(url=token_url, data=data)
                self.logger.debug("Request status code %s", res.status_code)
                res.raise_for_status()
            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.debug("Login error: %s", e.response.text)
                self.logger.error("Password flow authentication failed.")
                await self.handle_http_error(e, True)


            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in"],
                                         res.json()["refresh_token"])


        if connection_type == OAuth2ConnectionType.auth_code:
            
            if redirect_uri:
                self.redirect_uri = redirect_uri

            data = {'grant_type': 'authorization_code', 'code': auth_code, 'client_id': self.client_id, 'client_secret': self.client_secret, 'redirect_uri': self.redirect_uri}

            try:
                res = await self.http.post(url=token_url, data=data)
                res.raise_for_status()
            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.debug("Login error: %s", e.response.text)
                self.logger.error("Authorization code authentication failed.")
                await self.handle_http_error(e, True)

            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in"],
                                         res.json()["refresh_token"])

            self.logger.info("Established connection.")
            self.logger.debug("Access token valid: %s", self.connection.access_token_validity)



        if connection_type == OAuth2ConnectionType.refresh_token:

            if self.connection:
                refresh_token = self.connection.refresh_token
            if refresh_token == None:
                raise MissingCredentialsError(message='Missing refresh token.')

            data = {'grant_type': 'refresh_token', 'refresh_token': refresh_token, 'client_id': self.client_id, 'client_secret': self.client_secret}


            try:
                res = await self.http.post(url=token_url, data=data)
                res.raise_for_status()
            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.debug("Login error: %s", e.response.text)
                self.logger.error("Refresh token authentication failed.")
                await self.handle_http_error(e, True)


            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in"],
                                         res.json()["refresh_token"])

        self.connected = True
        self.http.headers["Authorization"] = "Bearer " + self.connection.access_token
  
        return self.connection

    async def disconnect(self):
        await self.http.aclose()
        await self.downloader.aclose()
        await self.uploader.aclose()

    def get_code_url(self):
        """ builds OAuth authorization code url to visit – requires OAuth app to use redirect uri ($host/oauth/callback or custom uri) """
        # generate URL string for OAuth auth code flow
        return self.base_url + f'/oauth/authorize?branding=full&response_type=code&client_id={self.client_id}&redirect_uri={self.redirect_uri}&scope=all'


    async def logout(self, revoke_refresh_token: bool = False):
        """ revoke tokens """
        revoke_url = self.base_url + '/oauth/revoke'
    
        access_data = {'token': self.connection.access_token, 'token_type_hint': 'access_token', 'client_id': self.client_id, 'client_secret': self.client_secret}
        refresh_data = {'token': self.connection.refresh_token, 'token_type_hint': 'refresh_token', 'client_id': self.client_id, 'client_secret': self.client_secret}

        try:
            res_a = await self.http.post(url=revoke_url, data=access_data)
            res_a.raise_for_status()
            if revoke_refresh_token:
                res_r = await self.http.post(url=revoke_url, data=refresh_data)
                res_r.raise_for_status()
        except httpx.RequestError as e:
            await self.handle_connection_error(e)
        except httpx.HTTPStatusError as e:
            self.logger.debug("Token revoke error: %s", e.response.text)
            self.logger.error("Revoking token(s) failed.")
            await self.handle_http_error(err=e, raise_on_err=self.raise_on_err)

        self.connected = False
        self.connection = None
        await self.disconnect()

    async def check_access_token(self, test: bool = False):
        """ check access token validity (based on connection time and token validity) """
        self.logger.debug("Testing access token validity.")
        self.logger.debug("Full authenticated test enabled: %s", test)

        if not test and self.connection:
            now = datetime.now()
            return (now - self.connection.connected_at).seconds < self.connection.access_token_validity
        elif test and self.connection:
            return await self.test_connection()
        else:
            self.logger.error("Access token no longer valid.")
            return False

    async def test_connection(self, test: bool = False) -> bool:
        """ test authenticated connection via authenticated ping """
        self.logger.debug("Testing authenticated connection.")

        if not self.connection or not self.connected:
            self.logger.critical("DRACOON connection not established.")
            return False

        if test:

            test_url = self.base_url + '/api/v4/user/ping'

            try:
                res = await self.http.get(url=test_url)
                res.raise_for_status()

            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.error("Authenticated ping failed.")
                await self.handle_http_error(err=e, raise_on_err=self.raise_on_err)
                return False
            
            return True

        return await self.check_access_token()


    async def handle_http_error(self, err: httpx.HTTPStatusError, raise_on_err: bool, is_xml: bool = False, close_client: bool = False, debug_content: bool = True):
        if self.raise_on_err:
            raise_on_err = self.raise_on_err
        
        self.logger.debug("HTTP request failed: %s", err.response.status_code)
        
        # handle AWS S3 XML responses
        if debug_content and not is_xml:
            self.logger.debug("%s", err.response.text)
        elif debug_content and is_xml:
            self.logger.debug("%s", err.response.content)

        if close_client:
            await self.disconnect()
        
        if raise_on_err:
            self.raise_http_error(err=err)

    async def handle_connection_error(self, err: httpx.RequestError):
        self.logger.critical("Connection error.")
        self.logger.critical(err.request.url)
        await self.disconnect()
        raise err
    
    async def handle_generic_error(self, err: Exception, close_client: bool = False):
        self.logger.critical("An error ocurred.")
        self.logger.debug("%s", err)
        if close_client:
            await self.disconnect()
        raise err

    def raise_http_error(self, err: httpx.HTTPStatusError):

        if err.response.status_code == 400:
            raise HTTPBadRequestError(error=err)
        if err.response.status_code == 401:
            raise HTTPUnauthorizedError(error=err)
        if err.response.status_code == 402:
            raise HTTPPaymentRequiredError(error=err)
        if err.response.status_code == 403:
            raise HTTPForbiddenError(error=err)
        if err.response.status_code == 404:
            raise HTTPNotFoundError(error=err)
        if err.response.status_code == 409:
            raise HTTPConflictError(error=err)
        if err.response.status_code == 412:
            raise HTTPPreconditionsFailedError(error=err)
        else:
            raise HTTPUnknownError(error=err)

        
        