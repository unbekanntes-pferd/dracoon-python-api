# ---------------------------------------------------------------------------#
# Python module to provide DRACOON object - contains a selection of
# basic API calls for scripting
# Version 1.0.1
# Author: Octavio Simone, 25.09.2020
# ---------------------------------------------------------------------------#


import json  # handle JSON
import requests  # HTTP requests
import base64  # base64 encode
import mimetypes

# define DRACOON class object with specific variables (clientID, clientSecret optional)
class dracoon:
    def __init__(self, clientID, clientSecret=None):
        self.clientID = clientID
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
        self.api_call_headers = {'Authorization': 'Bearer ' + oauth_token}

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
                self.api_call_headers = {'Authorization': 'Bearer ' + tokens['access_token']}
        if self.clientSecret is None:
            call_header = {'Authorization': 'Basic ' + token_payload.decode('ascii')}
            api_response = requests.post(token_url, data=data, allow_redirects=False, headers=call_header)
            if api_response.status_code == 200:
                tokens = json.loads(api_response.text)
                self.api_call_headers = {'Authorization': 'Bearer ' + tokens['access_token']}
        return api_response

    # get AD configs
    def get_ad_configs(self):
        api_url = self.apiURL + '/system/config/auth/ads'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        self.adConfigs = []
        if api_response.status_code == 200:
            for item in api_response.json()["items"]:
                self.adConfigs.append(item)
        return api_response

    # create basic user
    def create_basic_user(self, params):
        api_url = self.apiURL + '/users'
        api_response = requests.post(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # create Active Directory user
    def create_ad_user(self, params):
        api_url = self.apiURL + '/users'
        api_response = requests.post(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # assign a list of users to a group - requires group id
    def group_assign(self, groupID, userIDs):
        api_url = self.apiURL + '/groups/' + str(groupID) + '/users'

        # JSON payload
        group_assign = {
            'ids': userIDs
        }
        api_response = requests.post(api_url, headers=self.api_call_headers, json=group_assign)
        return api_response

    # get users for provided email address
    def get_user_by_email(self, email):
        api_url = self.apiURL + '/users?filter=email:eq:' + email
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get a user by provided userName
    def get_user_by_username(self, userName):
        api_url = self.apiURL + '/users?filter=userName:eq:' + userName
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get groups of a user or groups a user can be a member of
    def get_user_groups(self, userID, memberOnly=True):
        if memberOnly == True:
            api_url = self.apiURL + '/users/' + str(userID) + '/groups?filter=isMember:eq:true'
        else:
            api_url = self.apiURL + '/users/' + str(userID) + '/groups'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get users in DRACOON instance - user manager role required
    def get_users(self, offset=0):
        api_url = self.apiURL + '/users?offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get user details
    def get_user_details(self, userID):
        api_url = self.apiURL + '/users/' + str(userID)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get total user count
    def get_user_count(self):
        api_url = self.apiURL + '/users?offset=0'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        if api_response.status_code == 200:
            return api_response.json()["range"]["total"]
        else:
            return api_response

    # edit user information
    def set_user_details(self, userID, params):
        api_url = self.apiURL + '/users/' + str(userID)
        api_response = requests.put(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # delete user
    def delete_user(self, userID):
        api_url = self.apiURL + '/users/' + str(userID)
        api_response = requests.delete(api_url, headers=self.api_call_headers)
        return api_response

    # get users in DRACOON instance - user manager role required
    def get_groups(self, offset=0):
        api_url = self.apiURL + '/groups?offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # audit room permissions
    def audit_room_permissions(self, offset=0):
        api_url = self.apiURL + '/eventlog/audits/nodes?offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # audit room permission in parent node (room)
    def audit_room_permissions_parent(self, parentID):
        api_url = self.apiURL + '/eventlog/audits/nodes?filter=nodeParentId:eq:' + str(parentID) + '&offset=0'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get all events based on operation id
    def get_event_by_operation(self, operationID, startTime=None, endTime=None):
        api_response = []
        if startTime == None and endTime == None:
            api_url = self.apiURL + '/eventlog/events?type=' + str(operationID)
            api_response_total = requests.get(api_url, headers=self.api_call_headers)
            if api_response_total.status_code == 200:
                total_items = api_response_total.json()["range"]["total"]
                for offset in range(0, total_items, 500):
                    api_url = self.apiURL + '/eventlog/events?offset=' + str(offset) + '&type=' + str(operationID)
                    response = requests.get(api_url, headers=self.api_call_headers)
                    api_response.append(response.json())
                return api_response
        elif startTime != None and endTime == None:
            self.api_call_headers['X-Sds-Date-Format'] = 'EPOCH'
            api_url = self.apiURL + '/eventlog/events?date_start=' + str(startTime) + '&type=' + str(operationID)
            api_response_total = requests.get(api_url, headers=self.api_call_headers)
            if api_response_total.status_code == 200:
                total_items = api_response_total.json()["range"]["total"]
                for offset in range(0, total_items, 500):
                    api_url = self.apiURL + '/eventlog/events?date_start=' + str(startTime) + '&offset=' \
                              + str(offset) + '&type=' + str(operationID)
                    response = requests.get(api_url, headers=self.api_call_headers)
                    api_response.append(response.json())
                return api_response
        else:
            self.api_call_headers['X-Sds-Date-Format'] = 'EPOCH'
            api_url = self.apiURL + '/eventlog/events?date_end=' + str(endTime) + '&date_start=' \
                      + str(startTime) + '?type=' + str(operationID)
            api_response_total = requests.get(api_url, headers=self.api_call_headers)
            if api_response_total.status_code == 200:
                total_items = api_response_total.json()["range"]["total"]
                for offset in range(0, total_items, 500):
                    api_url = self.apiURL + '/eventlog/events?date_end=' + str(endTime) + '&date_start=' \
                              + str(startTime) + '&offset=' + str(offset) + '&type=' + str(operationID)
                    response = requests.get(api_url, headers=self.api_call_headers)
                    api_response.append(response.json())
                return api_response
        if api_response_total.status_code != 200:
            return api_response_total

    # get rooms in a given parent id (room or folder) - only rooms accessible are returned
    def get_rooms(self, parentID, roomManager="false", offset=0):
        api_url = self.apiURL + '/nodes?offset=' + str(offset) + '&room_manager=' + roomManager \
                  + '&filter=type:eq:room&parent_id=' + str(parentID)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get rooms with mange room permission
    def get_rooms_managed(self, parentID, offset=0):
        api_url = self.apiURL + '/nodes?offset=' + str(offset) + '&filter=type:eq:room|perm:eq:manage&parent_id=' \
                  + str(parentID)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get rooms in a given parent id (room or folder) - only rooms accessible are returned
    def get_room_log(self, roomID, offset=0):
        api_url = self.apiURL + '/nodes/rooms/' + str(roomID) + '/events/?offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get rooms in a given parent id (room or folder) - room manager view (only delete / rename / quota for managed
    # rooms)
    def get_rooms_manager(self, parentID, offset=0):
        api_url = self.apiURL + '/nodes?offset=' + str(offset) + '&filter=type:eq:room&parent_id=' \
                  + str(parentID) + '&room_manager=true'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # search data rooms
    def search_rooms(self, filter, parentID=None, depthLevel=0, offset=0):
        api_url = self.apiURL + '/nodes/search?search_string=' + filter + '&depth_level=' + str(depthLevel) \
                  + '&parent_id=' + str(parentID) + '&filter=type:eq:room&offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # search files
    def search_files(self, filter, parentID=None, depthLevel=0, offset=0):
        api_url = self.apiURL + '/nodes/search?search_string=' + filter + '&depth_level=' + str(depthLevel) \
                  + '&parent_id=' + str(parentID) + '&filter=type:eq:file&offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # search data rooms
    def search_folders(self, filter, parentID=None, depthLevel=0, offset=0):
        api_url = self.apiURL + '/nodes/search?search_string=' + filter + '&depth_level=' + str(depthLevel) \
                  + '&parent_id=' + str(parentID) + '&filter=type:eq:folder&offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

   # get pending room actions (accept new group members)
    def get_rooms_pending(self, offset=0):
        api_url = self.apiURL + '/nodes/rooms/pending?offset=' + str(offset)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

   # process pending room actions (accept new group members)
    def process_rooms_pending(self, params):
        api_url = self.apiURL + '/nodes/rooms/pending'
        api_response = requests.put(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # get files in a given parent id (room or folder)
    def get_files(self, parentID, offset=0):
        api_url = self.apiURL + '/nodes?offset=' + str(offset) + '&filter=type:eq:file&parent_id=' + str(parentID)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get folders and files in a given parent id (room or folder)
    def get_folders_files(self, parentID, offset=0):
        api_url = self.apiURL + '/nodes?offset=' + str(offset) + '&filter=type:eq:folder:file&parent_id=' + str(parentID)
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get a group id by name
    def get_group_by_name(self, name):
        api_url = self.apiURL + '/groups?filter=name:cn:' + name
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # create group with provided name
    def create_group(self, name):
        api_url = self.apiURL + '/groups'
        group_creator = {
            'name': name
        }
        api_response = requests.post(api_url, headers=self.api_call_headers, json=group_creator)
        return api_response

   # get groups assigned to a data room
    def get_room_groups(self, roomID, offset=0):
        api_url = self.apiURL + '/nodes/rooms/' + str(roomID) + '/groups?offset=' + str(offset) + '&filter=isGranted:eq:true'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # assign groups to a room
    def room_group_assign(self, roomID, params):
        api_url = self.apiURL + '/nodes/rooms/' + str(roomID) + '/groups'
        api_response = requests.put(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # create data room in parent node id - known id required - if root: set to 0
    def create_room(self, params):
        api_url = self.apiURL + '/nodes/rooms'
        api_response = requests.post(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # get customer info (quota used, user count..)
    def get_customer_info(self):
        api_url = self.apiURL + '/user/account/customer'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # get list of webhooks
    def get_webhooks(self):
        api_url = self.apiURL + '/settings/webhooks'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # create webhook (default enabled, trigger example event after creation)
    def create_webhook(self, params):
        api_url = self.apiURL + '/settings/webhooks'
        api_response = requests.post(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # edit a webhook by id
    def edit_webhook(self, webhookID, params):
        api_url = self.apiURL + '/settings/webhooks/' + str(webhookID)
        api_response = requests.put(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # reset liftetime of a webhook by id
    def reset_webhook_lifetime(self, webhookID):
        api_url = self.apiURL + '/settings/webhooks/' + str(webhookID) + '/reset_lifetime'
        api_response = requests.post(api_url, headers=self.api_call_headers)
        return api_response

    # delete webhook by id
    def delete_webhook(self, webhookID):
        api_url = self.apiURL + '/settings/webhooks/' + str(webhookID)
        api_response = requests.delete(api_url, headers=self.api_call_headers)
        return api_response

   # assign / unassign webhook to room
    def assign_webhook(self, roomID, params):
        api_url = self.apiURL + '/nodes/rooms/' + str(roomID) + '/webhooks'
        api_response = requests.put(api_url, headers=self.api_call_headers, json=params)
        return api_response

    # delete webhook by id
    def get_assigned_webhooks(self, roomID):
        api_url = self.apiURL + '/nodes/rooms/' + str(roomID) + '/webhooks'
        api_response = requests.get(api_url, headers=self.api_call_headers)
        return api_response

    # open upload channel (file upload step 1)
    def get_upload_channel(self, parentID, filename, filesize, classification=2):
        channel_url = self.apiURL + '/nodes/files/uploads'
        upload_data = {
            'parentId': parentID,
            'name': filename,
            'size': filesize,
            'classification': classification
        }
        channel_response = requests.post(channel_url, headers=self.api_call_headers, json=upload_data)
        return channel_response

    # upload file (file upload step 2)
    def upload_file(self, channel_response, file):

        if channel_response.status_code == 201:
            uploadURL = channel_response.json()['uploadUrl']
        else:
            return channel_response

        upload_header = {
            'accept': 'application/json'
        }
        file_uploader = {'file': file}


        upload_response = requests.post(uploadURL, headers=upload_header, files=file_uploader)
        return upload_response

    # finalize upload (file upload step 3)
    def finalize_upload(self, channel_response):

        upload_final_header = {
            'accept': 'application/json',
            'Content-Type': 'application/json'
        }
        if channel_response.status_code == 201:
            uploadURL = channel_response.json()['uploadUrl']
        else:
            return channel_response

        upload_final_response = requests.put(uploadURL, headers=upload_final_header)
        return upload_final_response

    def generate_download_url(self, nodeID):
        api_url = self.apiURL + '/nodes/files/' + str(nodeID) + '/downloads'

        api_response = requests.post(api_url, headers=self.api_call_headers)
        return api_response













