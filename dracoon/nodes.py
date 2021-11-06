"""
Async DRACOON nodes adapter based on httpx and pydantic
V1.0.0
(c) Octavio Simone, November 2021 

Collection of DRACOON API calls for nodes management
Documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/nodes

Please note: maximum 500 items are returned in GET requests 

 - refer to documentation for details on filtering and offset 
 - use documentation for payload description 


"""

import datetime
from typing import List, Union
import httpx
from pydantic import validate_arguments
from .crypto_models import FileKey
from .groups_models import Expiration
from .core import DRACOONClient, OAuth2ConnectionType
from .nodes_models import CompleteS3Upload, ConfigRoom, CreateFolder, CreateRoom, CreateUploadChannel, GetS3Urls, Permissions, ProcessRoomPendingUsers, S3Part, SetFileKeys, SetFileKeysItem, TransferNode, CommentNode, RestoreNode, UpdateFiles, UpdateFolder, UpdateRoom, UpdateRoomGroupItem, UpdateRoomGroups, UpdateRoomHooks, UpdateRoomUserItem, UpdateRoomUsers


class DRACOONNodes:

    """
    API wrapper for DRACOON nodes endpoint:
    Node operations (rooms, files, folders), room webhooks, comments and file transfer (up- and download)
    """

    def __init__(self, dracoon_client: DRACOONClient):
        """ requires a DRACOONClient to perform any request """
        if not isinstance(dracoon_client, DRACOONClient):
            raise TypeError('Invalid DRACOON client format.')
        if dracoon_client.connection:
            self.dracoon = dracoon_client
            self.api_url = self.dracoon.base_url + self.dracoon.api_base_url + '/nodes'
        else:
            raise ValueError(
                'DRACOON client must be connected: client.connect()')

    # get download url as authenticated user to download a file
    @validate_arguments
    async def create_upload_channel(self, upload_channel: CreateUploadChannel):
        """ create an upload channel to upload (S3 direct or proxy) """
        payload = upload_channel.dict(exclude_unset=True)

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + '/files/uploads'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res
    
    def make_upload_channel(self, parent_id: int, name: str, classification: int = None, size: int = None, expiration: Expiration = None, notes: str = None, 
                            direct_s3_upload: bool = None) -> CreateUploadChannel:
        """ make an upload channel payload for create_upload_channel() """
        upload_channel = {
            "parentId": parent_id,
            "name": name
        }

        if classification: upload_channel["classification"] = classification
        if size: upload_channel["size"] = size
        if expiration: upload_channel["expiration"] = expiration
        if notes: upload_channel["notes"] = notes
        if direct_s3_upload: upload_channel["directS3Upload"] = direct_s3_upload

        return upload_channel


    @validate_arguments
    async def cancel_upload(self, upload_id: str):
        """ cancel an upload channel (and delete chunks) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/uploads/{upload_id}'
        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    @validate_arguments
    async def complete_s3_upload(self, upload_id: int, upload: CompleteS3Upload):
        """ finalize an S3 direct upload """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/uploads/{upload_id}/s3'

        payload = upload.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_s3_upload_complete(self, parts: List[S3Part], resolution_strategy: str = None, keep_share_links: str = None, file_name: str = None, file_key: FileKey = None) -> CompleteS3Upload:
        """ make payload required in complete_s3_upload() """
        s3_upload_complete = {
            "parts": parts
        }

        if resolution_strategy: s3_upload_complete["resolutionStrategy"] = resolution_strategy
        if keep_share_links: s3_upload_complete["keepShareLinks"] = keep_share_links
        if file_name: s3_upload_complete["fileName"] = file_name
        if file_key: s3_upload_complete["fileKey"] = file_key
  
        return s3_upload_complete

    @validate_arguments
    async def get_s3_urls(self, upload_id: int, upload: GetS3Urls):
        """ get a list of S3 urls based on provided chunk count """
        """ chunk size needs to be larger than 5 MB """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/uploads/{upload_id}/s3_urls'

        payload = upload.dict()

        try:
            res = await self.dracoon.http.post(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    @validate_arguments
    async def get_nodes(self, room_manager: bool = False, parent_id: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
        """ list (all) visible nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/?offset={offset}&parent_id={str(parent_id)}&room_manager={str(room_manager).lower()}'
        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete nodes for given array of node ids

    @validate_arguments
    async def delete_nodes(self, node_list: List[int]):
        """ delete a list of nodes (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "nodeIds": node_list
        }

        try:
            res = await self.dracoon.http.request(method='DELETE', url=self.api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node for given node id
    @validate_arguments
    async def get_node(self, node_id: int):
        """ get specific node details (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res


    @validate_arguments
    async def delete_node(self, node_id: int):
        """ delete specific node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node comments for given node id
    @validate_arguments
    async def get_node_comments(self, node_id: int, offset: int = 0):
        """ get comments for specific node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/{str(node_id)}/comments/?offset={str(offset)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node for given node id
    @validate_arguments
    async def add_node_comment(self, node_id: int, comment: CommentNode):
        """ add a comment to a node """
        payload = comment.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}/comments'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_comment(self, text: str) -> CommentNode:
        """ make a comment payload for add_comment() """
        comment = {
            "text": text
        }

        return comment

    # copy node for given node id
    @validate_arguments
    async def copy_nodes(self, target_id: int, copy_node: TransferNode):
        """ copy node(s) to given target id """
        payload = copy_node.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(target_id)}/copy_to'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_node_transfer(self, items: List[int], resolution_strategy: str = None, keep_share_links: bool = None, parent_id: int = None) -> TransferNode:
        """ make a node transfer payload for copy_nodes() and move_nodes() """
        node_transfer = {
            "items": items
        }

        if resolution_strategy: node_transfer["resolutionStrategy"] = resolution_strategy
        if keep_share_links: node_transfer["keepShareLinks"] = keep_share_links
        if parent_id: node_transfer["parentId"] = parent_id
        
        return node_transfer


    # get node comfor given node id
    @validate_arguments
    async def get_deleted_nodes(self, parent_id: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
        """ list (all) deleted nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/{str(parent_id)}/deleted_nodes/?offset={offset}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # empty recycle bin of a given parent id

    @validate_arguments
    async def empty_node_recyclebin(self, parent_id: int):
        """ delete all nodes in recycle bin of parent (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(parent_id)}/deleted_nodes'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node versions in a given parent id (requires name, specification of type)
    @validate_arguments
    async def get_node_versions(self, parent_id: int, name: str = None, type: str = None, offset: int = 0):
        """ get (all) versions of a node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/{str(parent_id)}/deleted_nodes/versions?offset={offset}'

        if type != None:
            api_url += f'&type={type}'
        if name != None:
            api_url += f'&name={name}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node for given node id

    @validate_arguments
    async def add_favorite(self, node_id: int):
        """ add a specific node to favorites (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}/favorite'
        try:
            res = await self.dracoon.http.post(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete node for given node id
    @validate_arguments
    async def delete_favorite(self, node_id: int):
        """ remove a specific node from favorites (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}/favorite'

        try:
            res = await self.dracoon.http.delete(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # copy node for given node id
    @validate_arguments
    async def move_nodes(self, target_id: int, move_node: TransferNode):
        """ move node(s) to target node (by id) """
        payload = move_node.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(target_id)}/move_to'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node ancestors (parents)
    @validate_arguments
    async def get_parents(self, node_id: int):
        """ get node parents """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/{str(node_id)}/parents'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete deleted nodes in recycle bin for given array of node ids

    @validate_arguments
    async def empty_recyclebin(self, node_list: List[int]):
        """ empty recylce bin: list of nodes (deleted nodes by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "deletedNodeIds": node_list
        }

        try:
            res = await self.dracoon.http.request(method='DELETE', url=self.api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get deleted node info for given node id
    @validate_arguments
    async def get_deleted_node(self, node_id: int):
        """ get details of a specific deleted node (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/deleted_nodes/{str(node_id)}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # restore deleted nodes from recycle bin
    @validate_arguments
    async def restore_nodes(self, restore: RestoreNode):
        """ restore a list of nodes from recycle bin """
        payload = restore.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/deleted_nodes/actions/restore'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_node_restore(self, deleted_node_list: List[int], resolution_strategy: str = None, keep_share_links: bool = None, parent_id: int = None) -> RestoreNode:
        """ make payload required for restore_nodes() """
        node_restore = {
            "items": deleted_node_list
        }

        if resolution_strategy: node_restore["resolutionStrategy"] = resolution_strategy
        if keep_share_links: node_restore["keepShareLinks"] = keep_share_links
        if parent_id: node_restore["parentId"] = parent_id
        
        return node_restore

    # update file meta data
    @validate_arguments
    async def update_file(self, file_id: int, file_update: UpdateFiles):
        """ update file metadata """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/{str(file_id)}'

        payload = file_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res
    
    # get download url as authenticated user to download a file
    @validate_arguments
    async def get_download_url(self, node_id: int):
        """ get download url for a specific node """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/{str(node_id)}/downloads'
        try:
            res = await self.dracoon.http.post(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get user file key if available
    @validate_arguments
    async def get_user_file_key(self, file_id: int, version: str = None):
        """ get file key for given node as authenticated user """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/{str(file_id)}/user_file_key'

        if version: api_url += f'/?version={version}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    @validate_arguments
    async def set_file_keys(self, file_keys: SetFileKeys):
        """ set file keys for nodes """
        payload = file_keys.dict()

        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/files/keys'
        try:
            res = await self.dracoon.http.post(api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_set_file_keys(self, file_key_list: List[SetFileKeysItem]) -> SetFileKeys:
        """ make payload required for set_file_keys() """
        return {
            "items": file_key_list
        }
        

    def make_set_file_key_item(self, file_id: int, user_id: int, file_key: FileKey):
        """ make an entry to set a file key for a given file – required in make_set_file_keys() """
      
        return {
            "fileId": file_id,
            "userId": user_id, 
            "fileKey": file_key
        }


    # create folder
    @validate_arguments
    async def create_folder(self, folder: CreateFolder):
        """ create a new folder """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/folders'

        payload = folder.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_folder(self, name: str, parent_id: int, notes: str = None, created: datetime = None, updated: datetime = None) -> CreateFolder:
        """ make a folder payload required for create_folder() """
        folder = {
            "parentId": parent_id,
            "name": name
        }

        if notes: folder["notes"] = notes
        if created: folder["timestampCreation"] = created
        if updated: folder["timestampModification"] = updated

        return folder

    def make_folder_update(self, name: str = None, notes: str = None, created: datetime = None, updated: datetime = None) -> UpdateFolder:
        """" make a folder update payload for update_folder() """
        folder = {}
        
        if name: folder["name"] = notes
        if notes: folder["notes"] = notes
        if created: folder["timestampCreation"] = created
        if updated: folder["timestampModification"] = updated

        return folder

    # update folder mets data
    @validate_arguments
    async def update_folder(self, node_id: int, folder_update: UpdateFolder):
        """ update a folder """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/folders/{str(node_id)}'

        payload = folder_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get missing file keys
    @validate_arguments
    async def get_missing_file_keys(self, file_id: int = None, room_id: int = None, user_id: int = None, use_key: str = None, offset: int = 0, limit: int = None):
        """ get (all) missing file keys """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/missingFileKeys/?offset={str(offset)}'

        if file_id != None:
            api_url += f'&file_id={str(file_id)}'
        if room_id != None:
            api_url += f'&room_id={str(room_id)}'
        if user_id != None:
            api_url += f'&user_id={str(user_id)}'
        if use_key != None:
            api_url += f'&use_key={use_key}'
        if limit != None:
            api_url += f'&limit={str(limit)}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # create folder
    @validate_arguments
    async def create_room(self, room: CreateRoom):
        """ create a new room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms'

        payload = room.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # update room mets data
    @validate_arguments
    async def update_room(self, node_id: int, room_update: UpdateRoom):
        """ update a room (by id) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/{str(node_id)}'

        payload = room_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_room(self, name: str, parent_id: int = 0, notes: str = None, created: datetime = None, updated: datetime = None, 
                  quota: int = None, recycle_bin_period: int = None, inherit_perms: bool = None, classification: int = None, 
                  admin_ids: List[int] = None, admin_group_ids: List[int] = None, activities_log: bool = None,
                  new_group_member_acceptance: str = None) -> CreateRoom:
        """ make a room payload required for create_room() """
        room = {
            "parentId": parent_id,
            "name": name
        }
        
        if new_group_member_acceptance: room["newGroupMemberAcceptance"] = new_group_member_acceptance
        if quota: room["quota"] = quota
        if recycle_bin_period: room["recycleBinRetentionPeriod"] = recycle_bin_period
        if inherit_perms: room["inheritPermissions"] = inherit_perms
        if activities_log: room["hasActivitiesLog"] = activities_log
        if admin_ids: room["adminIds"] = admin_ids
        if admin_group_ids: room["adminGroupIds"] = admin_group_ids
        if notes: room["notes"] = notes
        if created: room["timestampCreation"] = created
        if updated: room["timestampModification"] = updated
        if classification: room["classification"] = classification

        if not admin_ids and not admin_group_ids:
            raise ValueError('Room admin required: Please provide at least one room admin.')

        return room

    def make_room_update(self, name: str = None, notes: str = None, qouta: int = None, created: datetime = None, updated: datetime = None, quota: int = None) -> UpdateRoom:
        """ make a room update payload for update_room() """
        room = {}
        
        if name: room["name"] = name
        if notes: room["notes"] = notes
        if quota: room["quota"] = quota
        if created: room["timestampCreation"] = created
        if updated: room["timestampModification"] = updated

        return room

    # configure data room
    @validate_arguments
    async def config_room(self, node_id: int, config_update: ConfigRoom):
        """ configure a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/{str(node_id)}/config'

        payload = config_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    def make_room_config(self, name: str = None, notes: str = None, created: datetime = None, updated: datetime = None, 
                        quota: int = None, recycle_bin_period: int = None, inherit_perms: bool = None, classification: int = None, 
                        admin_ids: List[int] = None, admin_group_ids: List[int] = None, activities_log: bool = None, 
                        new_group_member_acceptance: str = None) -> ConfigRoom:
        """ make a room config payload required for config_room() """
        room = {}
        
        if new_group_member_acceptance: room["newGroupMemberAcceptance"] = new_group_member_acceptance
        if quota: room["quota"] = quota
        if classification: room["classification"] = classification
        if recycle_bin_period: room["recycleBinRetentionPeriod"] = recycle_bin_period
        if inherit_perms: room["inheritPermissions"] = inherit_perms
        if activities_log: room["hasActivitiesLog"] = activities_log
        if admin_ids: room["adminIds"] = admin_ids
        if admin_group_ids: room["adminGroupIds"] = admin_group_ids
        if notes: room["notes"] = notes
        if created: room["timestampCreation"] = created
        if updated: room["timestampModification"] = updated
        if name: room["name"] = name

        return room

    def make_permissions(self, manage: bool, read: bool = True, create: bool = True,
                         change: bool = True, delete: bool = True, manage_shares: bool = True,
                         manage_file_requests: bool = True, read_recycle_bin: bool = True, 
                         restore_recycle_bin: bool = True, delete_recycle_bin: bool = False) -> Permissions:
        """ create a set of permissions for a room """
        return {
                             "manage": manage,
                             "read": read,
                             "create": create,
                             "change": change,
                             "delete": delete,
                             "manageDownloadShare": manage_shares,
                             "manageUploadShare": manage_file_requests,
                             "readRecycleBin": read_recycle_bin,
                             "restoreRecycleBin": restore_recycle_bin,
                             "deleteRecycleBin": delete_recycle_bin
                         }

    def make_permission_update(id: int, permission: Permissions) -> Union[UpdateRoomUserItem, UpdateRoomGroupItem]:
        """ make a permission update payload """
        
        return {
            "id": id,
            "permissions": permission

        }

    # get node comfor given node id
    @validate_arguments
    async def get_room_groups(self, node_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
        """ list (all) groups assigned to a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/rooms/{str(node_id)}/groups/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res


    @validate_arguments
    async def update_room_groups(self, node_id: int, groups_update: UpdateRoomGroups):
        """ bulk update assigned groups of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/{str(node_id)}/groups'

        payload = groups_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete groups assigned to room with given node id
    @validate_arguments
    async def delete_room_groups(self, room_id: int, group_list: List[int]):
        """ bulk delete assigned groups of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "ids": group_list
        }
        api_url = self.api_url + f'/rooms/{str(room_id)}/groups'

        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get node comfor given node id

    @validate_arguments
    async def get_room_users(self, node_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
        """ get (all) users assigned to a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/rooms/{str(node_id)}/users/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # add or change users assigned to room with given node id
    @validate_arguments
    async def update_room_users(self, node_id: int, users_update: UpdateRoomUsers):
        """ bulk update assigned users in a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/{str(node_id)}/users'

        payload = users_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete users assigned to room with given node id
    @validate_arguments
    async def delete_room_users(self, room_id: int, user_list: List[int]):
        """ bulk remove assigned users in a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        payload = {
            "ids": user_list
        }

        api_url = self.api_url + f'/rooms/{str(room_id)}/users'
        try:
            res = await self.dracoon.http.request(method='DELETE', url=api_url, json=payload, headers=self.dracoon.http.headers)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # get webhooks assigned or assignable to room with given node id
    @validate_arguments
    async def get_room_webhooks(self, node_id: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
        """" list (all) room webhooks """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/rooms/{str(node_id)}/webhooks/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # delete users assigned to room with given node id

    @validate_arguments
    async def update_room_webhooks(self, node_id: int, hook_update: UpdateRoomHooks):
        """ update room webhooks """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/{str(node_id)}/webhooks'

        payload = hook_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res


    @validate_arguments
    async def get_pending_assignments(self, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
        """ get pending room assignments (new group members not accepted) """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/pending/?offset={str(offset)}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res


    @validate_arguments
    async def process_pending_assignments(self, pending_update: ProcessRoomPendingUsers):
        """ procces (accept or reject) new group members of a room """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + f'/rooms/pending'

        payload = pending_update.dict()

        try:
            res = await self.dracoon.http.put(url=api_url, json=payload)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

    # search for nodes
    @validate_arguments
    async def search_nodes(self, search: str, parent_id: int = 0, depth_level: int = 0, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
        """ search for specific nodes """
        if not await self.dracoon.test_connection() and self.dracoon.connection:
            await self.dracoon.connect(OAuth2ConnectionType.refresh_token)

        api_url = self.api_url + \
            f'/search/?search_string={search}&offset={str(offset)}&parent_id={str(parent_id)}&depth_level={depth_level}'

        if filter != None:
            api_url += f'&filter={filter}'
        if limit != None:
            api_url += f'&limit={str(limit)}'
        if sort != None:
            api_url += f'&sort={sort}'

        try:
            res = await self.dracoon.http.get(api_url)
            print(res)

        except httpx.RequestError as e:
            raise httpx.RequestError(
                f'Connection to DRACOON failed: {e.request.url}')

        return res

"""
LEGACY API (0.4.x) - DO NOT MODIFY

"""

@validate_arguments
def get_nodes(roomManager: str = 'false', parentID: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):
    api_call = {
        'url': '/nodes?offset=' + str(offset) + '&parent_id=' + str(parentID) + '&room_manager=' + roomManager,
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# delete nodes for given array of node ids


@validate_arguments
def delete_nodes(nodeIDs: List[int]):
    api_call = {
        'url': '/nodes',
        'body': {
            "nodeIds": nodeIDs
        },
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get node for given node id


@validate_arguments
def get_node(nodeID: int):
    api_call = {
        'url': '/nodes/' + str(nodeID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# delete node for given node id


@validate_arguments
def delete_node(nodeID: int):
    api_call = {
        'url': '/nodes/' + str(nodeID),
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get node comments for given node id


@validate_arguments
def get_node_comments(nodeID: int, offset: int = 0):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/comments' + '/offset=' + offset,
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# get node for given node id


@validate_arguments
def add_node_comment(nodeID: int, params: CommentNode):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/comments',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# copy node for given node id


@validate_arguments
def copy_nodes(nodeID: int, params: TransferNode):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/copy_to',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get node comfor given node id


@validate_arguments
def get_deleted_nodes(parentID: int = 0, offset: int = 0, filter: str = None, limit: int = None, sort: str = None):

    api_call = {
        'url': '/nodes/' + str(parentID) + '/deleted_nodes?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# empty recycle bin of a given parent id


@validate_arguments
def empty_node_recyclebin(parentID: int):
    api_call = {
        'url': '/nodes/' + str(parentID) + '/deleted_nodes',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get node versions in a given parent id (requires name, specification of type)


@validate_arguments
def get_node_versions(parentID: int, name: str, type: str = 'file', offset: int = 0):
    api_call = {
        'url': '/nodes/' + str(parentID) + '/deleted_nodes/versions' + '/offset=' + offset + '&type=' + type + '&name=' + name,
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call


# get node for given node id
@validate_arguments
def add_favorite(nodeID: int):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/favorite',
        'body': None,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call


# delete node for given node id
@validate_arguments
def delete_favorite(nodeID: int):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/favorite',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# copy node for given node id


@validate_arguments
def move_nodes(nodeID: int, params: TransferNode):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/move_to',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get node ancestors (parents)


@validate_arguments
def get_parents(nodeID: int):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/parents',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# delete deleted nodes in recycle bin for given array of node ids


@validate_arguments
def empty_recyclebin(nodeIDs: List[int]):
    api_call = {
        'url': '/nodes/deleted_nodes',
        'body': {
            "deletedNodeIds": nodeIDs
        },
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get deleted node info for given node id


@validate_arguments
def get_deleted_node(nodeID: int):
    api_call = {
        'url': '/nodes/deleted_nodes/' + str(nodeID),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    return api_call

# restore deleted nodes from recycle bin


@validate_arguments
def restore_nodes(params: RestoreNode):
    api_call = {
        'url': '/nodes/deleted_nodes/actions/restore',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# update file meta data


@validate_arguments
def update_file(nodeID: int, params: UpdateFiles):
    api_call = {
        'url': '/nodes/files/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# get download url as authenticated user to download a file


@validate_arguments
def get_download_url(nodeID: int):
    api_call = {
        'url': '/nodes/files/' + str(nodeID) + '/downloads',
        'body': None,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# get user file key if available


@validate_arguments
def get_user_file_key(fileID: int, version: str = None):
    api_call = {
        'url': '/nodes/files/' + str(fileID) + '/user_file_key',
        'method': 'GET',
        'content_type': 'application/json'
    }

    if version != None:
        api_call['url'] += '/?version=' + version

    return api_call


@validate_arguments
def set_file_keys(params: SetFileKeys):
    api_call = {
        'url': '/nodes/files/keys',
        'method': 'POST',
        'body': params,
        'content_type': 'application/json'
    }
    return api_call

# get download url as authenticated user to download a file


@validate_arguments
def create_upload_channel(params: CreateUploadChannel):
    api_call = {
        'url': '/nodes/files/uploads',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# create folder


@validate_arguments
def create_folder(params: CreateFolder):
    api_call = {
        'url': '/nodes/folders',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# update folder mets data


@validate_arguments
def update_folder(nodeID: int, params: UpdateFolder):
    api_call = {
        'url': '/nodes/folders/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# get missing file keys


@validate_arguments
def get_missing_file_keys(fileID: int = None, roomID: int = None, userID: int = None, offset: int = 0, limit: int = None, use_key: str = None):
    api_call = {
        'url': '/nodes/missingFileKeys/?offset=' + str(offset),
        'method': 'GET',
        'content_type': 'application/json'
    }

    if roomID != None:
        api_call['url'] += '&room_id=' + str(roomID)
    if fileID != None:
        api_call['url'] += '&file_id=' + str(fileID)
    if userID != None:
        api_call['url'] += '&user_id=' + str(userID)

    return api_call


# create folder
@validate_arguments
def create_room(params: CreateRoom):
    api_call = {
        'url': '/nodes/rooms',
        'body': params,
        'method': 'POST',
        'content_type': 'application/json'
    }
    return api_call

# update room mets data


@validate_arguments
def update_room(nodeID: int, params: UpdateRoom):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# configure data room


@validate_arguments
def config_room(nodeID: int, params: ConfigRoom):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/config',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# get node comfor given node id


@validate_arguments
def get_room_groups(nodeID: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):

    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/groups?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# add or change groups assigned to room with given node id


@validate_arguments
def update_room_groups(nodeID: int, params: UpdateRoomGroups):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/groups',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete groups assigned to room with given node id


@validate_arguments
def delete_room_groups(nodeID: int):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/groups',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get node comfor given node id


@validate_arguments
def get_room_users(nodeID: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/users?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# add or change users assigned to room with given node id


@validate_arguments
def update_room_users(nodeID: int, params: UpdateRoomUsers):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/users',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# delete users assigned to room with given node id


@validate_arguments
def delete_room_users(nodeID: int):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/users',
        'body': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call

# get webhooks assigned or assignable to room with given node id


@validate_arguments
def get_room_webhooks(nodeID: int, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/webhooks?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# delete users assigned to room with given node id


@validate_arguments
def update_room_webhooks(nodeID: int, params: UpdateRoomHooks):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/webhooks',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# get pending room assignments (new group members not currently accepted)


@validate_arguments
def get_pending_assignments(offset: int = 0, filter: str = None, limit: str = None, sort: str = None):
    api_call = {
        'url': '/nodes/rooms/pending?offset=' + str(offset),
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }

    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call

# process pending room assignments


@validate_arguments
def process_pending_assignments(params: ProcessRoomPendingUsers):
    api_call = {
        'url': '/nodes/rooms/pending',
        'body': params,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    return api_call

# search for nodes


@validate_arguments
def search_nodes(search: str, parentID: int = 0, depthLevel: int = 0, offset: int = 0, filter: str = None, limit: str = None, sort: str = None):

    api_call = {
        'url': '/nodes/search?search_string=' + str(search) + '&offset=' + str(offset) +
        '&parent_id=' + str(parentID) + '&depth_level=' +
        str(depthLevel) + '&sort=parentPath:asc',
        'body': None,
        'method': 'GET',
        'content_type': 'application/json'
    }
    if filter != None:
        api_call['url'] += '&filter=' + filter
    if limit != None:
        api_call['url'] += '&limit=' + str(limit)
    if sort != None:
        api_call['url'] += '&sort=' + sort

    return api_call
