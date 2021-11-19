"""
Async DRACOON client based on httpx
V1.0.0

(c) Octavio Simone, November 2021 

The client implements all login and logout procedures and is part of every API adapter.

"""
import json  
import requests  
import base64 
import httpx
from enum import Enum
from dataclasses import dataclass
import base64
import asyncio
from datetime import datetime
from pydantic import validate_arguments, HttpUrl
import logging

from .core_models import ApiCall, ApiDestination, CallMethod, model_to_JSON

USER_AGENT = 'dracoon-python-1.0.0-alpha3'

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
    refresh_token_validity: int


class DRACOONClient:
    """ DRACOON client with an httpx async client """
    """ requires OAuth connection details and base url """
    api_base_url = '/api/v4'
    branding_base_url = '/branding/api'
    reporting_base_url = '/reporting/api'
    headers = {
        "User-Agent": USER_AGENT

    }

    def __init__(self, base_url: str, client_id: str = 'dracoon_legacy_scripting', client_secret: str = '', raise_on_err: bool = False):
        """ client is initialized with DRACOON instance details (url and OAuth client credentials) """
        self.base_url = base_url
        self.client_id = client_id
        self.client_secret = client_secret
        self.http = httpx.AsyncClient(headers=self.headers, timeout=30)
        self.connected = False
        self.connection: DRACOONConnection = None
        self.raise_on_err = raise_on_err
        self.logger = logging.getLogger('dracoon.client')

        self.logger.info("DRACOON client created.")
        self.logger.debug(f"DRACOON client config: {self.base_url} // {self.client_id}")

    def __del__(self):
        """ on client destroy terminate async client """
        loop = asyncio.get_event_loop()

        if loop.is_running():
            loop.create_task(self.http.aclose())
        else:
             loop.run_until_complete(self.http.aclose())
        

    async def connect(self, connection_type: OAuth2ConnectionType, username: str = None, password: str = None, auth_code: str = None) -> DRACOONConnection:
        """ connects based on given OAuth2ConnectionType """
        token_url = self.base_url + '/oauth/token'
        now = datetime.now()

        self.logger.debug("Establishing DRACOON connection...")
        
        # handle missing credentials for password flow
        if connection_type == OAuth2ConnectionType.password_flow and username == None and password == None:
            await self.http.aclose()
            self.logger.error("Missing credentials for OAuth2 password flow.")
            raise ValueError(
                'Username and password are mandatory for OAuth2 password flow.')

        # handle missing auth code for authorization code flow 
        if connection_type == OAuth2ConnectionType.auth_code and auth_code == None:
            await self.http.aclose()
            self.logger.error("Missing auth code for OAuth2 password flow.")
            raise ValueError(
                'Auth code is mandatory for OAuth2 authorization code flow.')

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


            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in_inactive"],
                                         res.json()["refresh_token"], res.json()["expires_in"])


        if connection_type == OAuth2ConnectionType.auth_code:

            data = {'grant_type': 'authorization_code', 'code': auth_code, 'client_id': self.client_id, 'client_secret': self.client_secret, 'redirect_uri': self.base_url + '/oauth/callback'}

            try:
                res = await self.http.post(url=token_url, data=data)
                res.raise_for_status()
            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.debug("Login error: %s", e.response.text)
                self.logger.error("Authorization code authentication failed.")
                await self.handle_http_error(e, True)

            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in_inactive"],
                                         res.json()["refresh_token"], res.json()["expires_in"])

            self.logger.info("Established connection.")
            self.logger.debug("Access token valid: %s", self.connection.access_token_validity)
            self.logger.debug("Refresh token valid: %s", self.connection.refresh_token_validity)


        if connection_type == OAuth2ConnectionType.refresh_token:
            data = {'grant_type': 'refresh_token', 'refresh_token': self.connection.refresh_token, 'client_id': self.client_id, 'client_secret': self.client_secret}


            try:
                res = await self.http.post(url=token_url, data=data)
                res.raise_for_status()
            except httpx.RequestError as e:
                await self.handle_connection_error(e)

            except httpx.HTTPStatusError as e:
                self.logger.debug("Login error: %s", e.response.text)
                self.logger.error("Refresh token authentication failed.")
                await self.handle_http_error(e, True)


            self.connection = DRACOONConnection(now, res.json()["access_token"], res.json()["expires_in_inactive"],
                                         res.json()["refresh_token"], res.json()["expires_in"])

        self.connected = True
        self.http.headers["Authorization"] = "Bearer " + self.connection.access_token
  

        return self.connection

    async def disconnect(self):
        await self.http.aclose()

    def get_code_url(self):
        """ builds OAuth authorization code url to visit – requires OAuth app to use redirect uri ($host/oauth/callback) """
        # generate URL string for OAuth auth code flow
        return self.base_url + f'/oauth/authorize?branding=full&response_type=code&client_id={self.client_id}&redirect_uri={self.base_url}/oauth/callback&scope=all'


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
            self.handle_http_error(err=e, raise_on_err=self.raise_on_err)

        self.connected = False
        self.connection = None
        await self.http.aclose()

    
    async def check_access_token(self, test: bool = False):
        """ check access token validity (based on connection time and token validity) """
        self.logger.info("Testing access token validity.")
        self.logger.debug("Full authenticated test enabled: %s", test)

        if not test and self.connection:
            now = datetime.now()
            return (now - self.connection.connected_at).seconds < self.connection.access_token_validity
        elif test and self.connection:
            return await self.test_connection()
        else:
            self.logger.error("Access token no longer valid.")
            return False

    def check_refresh_token(self):
        """ check refresh token validity (based on connection time and token validity) """
        self.logger.info("Testing access token validity.")

        if self.connection:
            now = datetime.now()
            return (now - self.connection.connected_at).seconds < self.connection.refresh_token_validity
        else:
            self.logger.error("Refresh token no longer valid.")
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


    async def handle_http_error(self, err: httpx.HTTPStatusError, raise_on_err: bool):
        if self.raise_on_err:
            raise_on_err = self.raise_on_err
        
        self.logger.error("HTTP request failed: %s", err.response.status_code)
        self.logger.debug("%s", err.response.text)
        
        if raise_on_err:
            await self.http.aclose()
            raise err

    async def handle_connection_error(self, err: httpx.RequestError):
        self.logger.critical("Connection error.")
        self.logger.critical(err.request.url)
        await self.http.aclose()
        raise err






"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

# define DRACOON class object with specific variables (clientID, clientSecret optional)
class Dracoon:
    def __init__(self, clientID: str, clientSecret: str = None):
        self.clientID = clientID

        self.api_call_headers = {'User-Agent': USER_AGENT}
        if clientSecret is not None:
            self.clientSecret = clientSecret
        if clientSecret is None:
            self.clientSecret = None

    # generate URls necessary for API calls based on passed baseURL
    @validate_arguments
    def set_URLs(self, baseURL: HttpUrl):
        self.baseURL = baseURL
        self.apiURL = baseURL + '/api/v4'
        self.reportingURL = baseURL + '/reporting/api'
        self.brandingURL = baseURL + '/branding/api'

    # pass oauth token - needed for OAuth2 three-legged flow
    @validate_arguments
    def pass_oauth_token(self, oauth_token: str):
        self.api_call_headers["Authorization"] = 'Bearer ' + oauth_token

    # authenticate via basic auth (local, AD) - if initiated without clientSecret, perform Basic auth, else authorize
    # via clientID & clientSecret
    @validate_arguments
    def basic_auth(self, userName: str, userPassword: str):
        data = {'grant_type': 'password', 'username': userName, 'password': userPassword}
        token_url = self.baseURL + '/oauth/token'
        token_payload = base64.b64encode(bytes(self.clientID + ':', 'ascii'))
        if self.clientSecret is not None:
            api_response = requests.post(token_url, data=data, allow_redirects=False,
                                         auth=(self.clientID, self.clientSecret))
            if api_response.status_code == 200:
                tokens = json.loads(api_response.text)
                self.api_call_headers["Authorization"] = 'Bearer ' + tokens["access_token"]
        if self.clientSecret is None:
            call_header = {'Authorization': 'Basic ' + token_payload.decode('ascii')}
            api_response = requests.post(token_url, data=data, allow_redirects=False, headers=call_header)
            if api_response.status_code == 200:
                tokens = json.loads(api_response.text)
                self.api_call_headers["Authorization"] = 'Bearer ' + tokens["access_token"]
        return api_response

    # generate URL string for OAuth auth code flow
    def get_code_url(self):
        return self.baseURL + f'/oauth/authorize?branding=full&response_type=code&client_id={self.clientID}&redirect_uri={self.baseURL}/oauth/callback&scope=all'

    # authenticate via code
    @validate_arguments
    def oauth_code_auth(self, code: str):
        data = {'grant_type': 'authorization_code', 'code': code, 'client_id': self.clientID, 'client_secret': self.clientSecret, 'redirect_uri': self.baseURL + '/oauth/callback'}
        token_url = self.baseURL + '/oauth/token'

        api_response = requests.post(token_url, data=data, headers=self.api_call_headers)
        if api_response.status_code == 200:
            self.tokens = json.loads(api_response.text)
            self.api_call_headers["Authorization"] = 'Bearer ' + self.tokens["access_token"]
        
        return api_response

    # get new tokens via refresh token
    def refresh_token_auth(self):
        token_url = self.baseURL + '/oauth/token'
        data = {'grant_type': 'refresh_token', 'refresh_token': self.tokens['refresh_token'], 'client_id': self.clientID, 'client_secret': self.clientSecret}
        
        api_response = requests.post(token_url, data=data, headers=self.api_call_headers)

        if api_response.status_code == 200:
            self.tokens = json.loads(api_response.text)
            self.api_call_headers["Authorization"] = 'Bearer ' + self.tokens["access_token"]

        return api_response

         
    # call handlers for GET, POST, PUT, DELETE 

    def get(self, api_call: ApiCall):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == CallMethod.GET.value:
            # handle different API endpoints 
            if "destination" in api_call:
                if api_call["destination"] == ApiDestination.Reporting:
                    api_url = self.reportingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Branding:
                    api_url = self.brandingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Core:
                    api_url = self.apiURL + api_call["url"]
            else:
                api_url = self.apiURL + api_call["url"]

            if "body" in api_call and api_call["body"] != None:
                api_response = requests.get(api_url, json=model_to_JSON(api_call["body"]), headers=self.api_call_headers)
            else:
                api_response = requests.get(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')
    
    def post(self, api_call: ApiCall):
        
        if api_call["method"] == CallMethod.POST.value and 'body' in api_call:
            self.api_call_headers["Content-Type"] = api_call["content_type"]
            
            # handle different API endpoints 
            if "destination" in api_call:
                if api_call["destination"] == ApiDestination.Reporting:
                    api_url = self.reportingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Branding:
                    api_url = self.brandingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Core:
                    api_url = self.apiURL + api_call["url"]
            else:
                api_url = self.apiURL + api_call["url"]

            if api_call["body"] != None:
                api_response = requests.post(api_url, json=model_to_JSON(api_call["body"]), headers=self.api_call_headers)
            else:
                api_response = requests.post(api_url, headers=self.api_call_headers)
            return api_response
        # check for API call with files instead of body - see uploads 
        if api_call["method"] == CallMethod.POST.value and 'files' in api_call:
            api_url = api_call["url"]
            if api_call["files"] != None:
                file_upload_header = {
                    "accept": "application/json",
                    "User-Agent": USER_AGENT
                }
                
                # required for chunked upload 
                if "Content-Range" in api_call and "Content-Length" in api_call:
                    file_upload_header["Content-Length"] = api_call["Content-Length"]
                    file_upload_header["Content-Range"] = api_call["Content-Range"]

                api_response = requests.post(api_url, headers=file_upload_header, files=api_call["files"])
            else:
                raise ValueError('No file to upload provided.')
            return api_response
        
        else:
            raise TypeError('Invalid request method.')
    

    def put(self, api_call: ApiCall):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == CallMethod.PUT.value:
                        # handle different API endpoints 
            if "destination" in api_call:
                if api_call["destination"] == ApiDestination.Reporting:
                    api_url = self.reportingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Branding:
                    api_url = self.brandingURL + api_call["url"]
                elif api_call["destination"] == ApiDestination.Core:
                    api_url = self.apiURL + api_call["url"]
            else:
                api_url = self.apiURL + api_call["url"]
 
            if "files" in api_call: api_url = api_call["url"]
            if api_call["body"] != None:
                api_response = requests.put(api_url, json=model_to_JSON(api_call["body"]), headers=self.api_call_headers)
            else:
                api_response = requests.put(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')

  
    def delete(self, api_call: ApiCall):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == CallMethod.DELETE.value:
            if "body" in api_call: api_url = self.apiURL + api_call["url"] 
            if "files" in api_call: api_url = api_call["url"]

            if api_call["body"] != None:
                api_response = requests.delete(api_url, json=model_to_JSON(api_call["body"]), headers=self.api_call_headers)
            else:
                api_response = requests.delete(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')

        # async call handlers for async requests (GET, POST, PUT, DELETE)

    async def async_get(self, api_call: ApiCall, session):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == "GET":
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                async with session.get(api_url, json=api_call["body"], headers=self.api_call_headers) as api_response:
                    return await api_response.text()
            else:
                async with session.get(api_url, headers=self.api_call_headers) as api_response:
                    return await api_response.text()  
        else:
            raise TypeError('Invalid request method.')
    
    async def async_post(self, api_call: ApiCall, session):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == "GET":
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                async with session.post(api_url, json=api_call["body"], headers=self.api_call_headers) as api_response:
                    return await api_response.text()
            if "files" in api_call and api_call["files"] != None:

                file_upload_header = {
                    "accept": "application/json"
                }
                async with session.post(api_url, headers=file_upload_header, files=api_call["files"]) as api_response:
                    return await api_response.text()
            else:
                async with session.post(api_url, headers=self.api_call_headers) as api_response:
                    return await api_response.text()  
        else:
            raise TypeError('Invalid request method.')
    

    async def async_put(self, api_call: ApiCall, session):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == "GET":
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                async with session.put(api_url, json=api_call["body"], headers=self.api_call_headers) as api_response:
                    return await api_response.text()
            else:
                async with session.put(api_url, headers=self.api_call_headers) as api_response:
                    return await api_response.text()  
        else:
            raise TypeError('Invalid request method.')
    
    async def async_delete(self, api_call: ApiCall, session):
        self.api_call_headers["Content-Type"] = api_call["content_type"]
        if api_call["method"] == "GET":
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                async with session.delete(api_url, json=api_call["body"], headers=self.api_call_headers) as api_response:
                    return await api_response.text()
            else:
                async with session.delete(api_url, headers=self.api_call_headers) as api_response:
                    return await api_response.text()  
        else:
            raise TypeError('Invalid request method.')






