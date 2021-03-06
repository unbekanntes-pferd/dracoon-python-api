# ---------------------------------------------------------------------------#
# Python module to provide DRACOON object
# Authentication and call handlers 
# Version 0.3.0
# Author: Octavio Simone, 06.03.2021
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


import json  # handle JSON
import requests  # HTTP requests
import base64  # base64 encode
import mimetypes
import aiohttp
import asyncio

# define DRACOON class object with specific variables (clientID, clientSecret optional)
class Dracoon:
    def __init__(self, clientID, clientSecret=None):
        self.clientID = clientID
        self.api_call_headers = {'User-Agent': 'dracoon-python-0.3.0'}
        if clientSecret is not None:
            self.clientSecret = clientSecret
        if clientSecret is None:
            self.clientSecret = None
    

    # generate URls necessary for API calls based on passed baseURL
    def set_URLs(self, baseURL):
        self.baseURL = baseURL
        self.apiURL = baseURL + '/api/v4'

    # pass oauth token - needed for OAuth2 three-legged flow
    def pass_oauth_token(self, oauth_token):
        self.api_call_headers["Authorization"] = 'Bearer ' + oauth_token

    # authenticate via basic auth (local, AD) - if initiated without clientSecret, perform Basic auth, else authorize
    # via clientID & clientSecret
    def basic_auth(self, userName, userPassword):
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
    def oauth_code_auth(self, code):
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
    def get(self, api_call):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
        if api_call["method"] == "GET":
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                api_response = requests.get(api_url, json=api_call["body"], headers=self.api_call_headers)
            else:
                api_response = requests.get(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')

    def post(self, api_call):
        if api_call["method"] == "POST" and "body" in api_call:
            self.api_call_headers["Content-Type"] = api_call["Content-Type"]
            api_url = self.apiURL + api_call["url"]
            if api_call["body"] != None:
                api_response = requests.post(api_url, json=api_call["body"], headers=self.api_call_headers)
            else:
                api_response = requests.post(api_url, headers=self.api_call_headers)
            return api_response
        # check for API call with files instead of body - see uploads 
        if api_call["method"] == "POST" and "files" in api_call:
            api_url = api_call["url"]
            if api_call["files"] != None:
                file_upload_header = {
                    "accept": "application/json",
                    "User-Agent": "dracoon-python-0.1.0"
                }
                api_response = requests.post(api_url, headers=file_upload_header, files=api_call["files"])
            else:
                raise ValueError('No file to upload provided.')
            return api_response
        else:
            raise TypeError('Invalid request method.')

    def put(self, api_call):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
        if api_call["method"] == "PUT":
            if "body" in api_call: api_url = self.apiURL + api_call["url"] 
            if "files" in api_call: api_url = api_call["url"]
            if api_call["body"] != None:
                api_response = requests.put(api_url, json=api_call["body"], headers=self.api_call_headers)
            else:
                api_response = requests.put(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')

    def delete(self, api_call):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
        if api_call["method"] == "DELETE":
            if "body" in api_call: api_url = self.apiURL + api_call["url"] 
            if "files" in api_call: api_url = api_call["url"]

            if api_call["body"] != None:
                api_response = requests.delete(api_url, json=api_call["body"], headers=self.api_call_headers)
            else:
                api_response = requests.delete(api_url, headers=self.api_call_headers)
            return api_response
        else:
            raise TypeError('Invalid request method.')

        # async call handlers for async requests (GET, POST, PUT, DELETE)
    async def async_get(self, api_call, session):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
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

    async def async_post(self, api_call, session):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
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

    async def async_put(self, api_call, session):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
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

    async def async_delete(self, api_call, session):
        self.api_call_headers["Content-Type"] = api_call["Content-Type"]
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

    


