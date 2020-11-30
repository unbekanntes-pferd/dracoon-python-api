# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for nodes access
# Requires Dracoon call handlers
# Version 0.1.0
# Author: Octavio Simone, 04.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#


# collection of DRACOON API calls for node access
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/nodes
# Please note: maximum 500 items are returned in GET requests 
# - refer to documentation for details on filtering and offset 
# - use documentation for payload description 
# All requests with bodies use generic params variable to pass JSON body

def get_nodes(roomManager='false', parentID=0, offset=0, filter=None, limit=None, sort=None):
    api_call = {
            'url': '/nodes?offset=' + str(offset) + '&parent_id=' + str(parentID) + '&room_manager=' + roomManager,
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }

    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
 
    return api_call

# delete nodes for given array of node ids
def delete_nodes(nodeIDs):
    api_call = {
        'url': '/nodes',
        'body': {
            "nodeIds": nodeIDs
        },
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get node for given node id
def get_node(nodeID):
    api_call = {
        'url': '/nodes/' + str(nodeID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# delete node for given node id
def delete_node(nodeID):
    api_call = {
        'url': '/nodes/' + str(nodeID),
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get node comments for given node id
def get_node_comments(nodeID, offset=0):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/comments' + '/offset=' + offset,
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# get node for given node id
def add_node_comment(nodeID, params):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/comments',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# copy node for given node id
def copy_nodes(nodeID, params):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/copy_to',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# get node comfor given node id
def get_deleted_nodes(parentID, offset=0, filter=None, limit=None, sort=None):
    
    api_call = {
            'url': '/nodes/' + str(parentID) + '/deleted_nodes?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }

    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# empty recycle bin of a given parent id
def empty_node_recyclebin(parentID):
    api_call = {
        'url': '/nodes/' + str(parentID) + '/deleted_nodes',
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get node versions in a given parent id (requires name, specification of type)
def get_node_versions(parentID, name, type='file', offset=0):
    api_call = {
        'url': '/nodes/' + str(parentID) + '/deleted_nodes/versions' + '/offset=' + offset + '&type=' + type + '&name=' + name,
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call


# get node for given node id
def add_favorite(nodeID):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/favorite',
        'body': None,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call


# delete node for given node id
def delete_favorite(nodeID):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/favorite',
        'body': None,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# copy node for given node id
def move_nodes(nodeID, params):
    api_call = {
        'url': '/nodes/' + str(nodeID) + '/move_to',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# delete deleted nodes in recycle bin for given array of node ids
def empty_recyclebin(nodeIDs):
    api_call = {
        'url': '/nodes',
        'body': {
            "nodeIds": nodeIDs
        },
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get deleted node info for given node id
def get_deleted_node(nodeID):
    api_call = {
        'url': '/nodes/deleted_nodes/' + str(nodeID),
        'body': None,
        'method': 'GET',
        'Content-Type': 'application/json'
    }
    return api_call

# restore deleted nodes from recycle bin
def restore_nodes(params):
    api_call = {
        'url': '/nodes/deleted_nodes/actions/restore',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# update file meta data
def update_file(nodeID, params):
    api_call = {
        'url': '/nodes/files/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# get download url as authenticated user to download a file
def get_download_url(nodeID):
    api_call = {
        'url': '/nodes/files' + str(nodeID) + '/downloads',
        'body': None,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# get download url as authenticated user to download a file
def create_upload_channel(params):
    api_call = {
        'url': '/nodes/files/uploads',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# create folder
def create_folder(params):
    api_call = {
        'url': '/nodes/folders',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# update folder mets data
def update_folder(nodeID, params):
    api_call = {
        'url': '/nodes/folders/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# create folder
def create_room(params):
    api_call = {
        'url': '/nodes/rooms',
        'body': params,
        'method': 'POST',
        'Content-Type': 'application/json'
    }
    return api_call

# update room mets data
def update_room(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID),
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# configure data room
def config_room(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/config',
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# get node comfor given node id
def get_room_groups(nodeID, offset=0, filter=None, limit=None, sort=None):

    api_call = {
            'url': '/nodes/rooms/' + str(nodeID) + '/groups?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# add or change groups assigned to room with given node id
def update_room_groups(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/groups',
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete groups assigned to room with given node id
def delete_room_groups(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/groups',
        'body': params,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get node comfor given node id
def get_room_users(nodeID, offset=0, filter=None, limit=None, sort=None):
    api_call = {
            'url': '/nodes/rooms/' + str(nodeID) + '/users?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort
 
    return api_call

# add or change users assigned to room with given node id
def update_room_users(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/users',
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# delete users assigned to room with given node id
def delete_room_users(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/users',
        'body': params,
        'method': 'DELETE',
        'Content-Type': 'application/json'
    }
    return api_call

# get webhooks assigned or assignable to room with given node id
def get_room_webhooks(nodeID, offset=0, filter=None, limit=None, sort=None):
    api_call = {
            'url': '/nodes/rooms/' + str(nodeID) + '/webhooks?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call

# delete users assigned to room with given node id
def update_room_webhooks(nodeID, params):
    api_call = {
        'url': '/nodes/rooms/' + str(nodeID) + '/webhooks',
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# get pending room assignments (new group members not currently accepted)
def get_pending_assignments(offset=0, filter=None, limit=None, sort=None):
    api_call = {
            'url': '/nodes/rooms/pending?offset=' + str(offset),
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    
    if filter != None: api_call['url'] += '&filter=' + filter

    return api_call

# process pending room assignments
def process_pending_assignments(params):
    api_call = {
        'url': '/nodes/rooms/pending',
        'body': params,
        'method': 'PUT',
        'Content-Type': 'application/json'
    }
    return api_call

# search for nodes
def search_nodes(search, parentID=0, depthLevel=0, offset=0, filter=None, limit=None, sort=None):
    
    api_call = {
            'url': '/nodes/search?search_string=' + str(search) +  '&offset=' + str(offset) + 
            '&parent_id=' + str(parentID)  + '&depth_level=' + str(depthLevel) + '&sort=parentPath:asc',
            'body': None,
            'method': 'GET',
            'Content-Type': 'application/json'
        }
    if filter != None: api_call['url'] += '&filter=' + filter
    if limit != None: api_call['url'] += '&limit=' + str(limit)
    if sort != None: api_call['url'] += '&sort=' + sort

    return api_call










