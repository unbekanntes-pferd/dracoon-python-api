"""
Script to convert all folders in a room to rooms with inheritance
Recursively converts all folders into rooms

Usage: 
folder_to_room.py -p "/Path/to/root" -d 1

-p / --path - path to room in DRACOON serving as root
-d / --depth - depth level (-1 for all levels)

27.10.2022 Octavio Simone
"""


import argparse
import sys
import asyncio
from pathlib import Path
from getpass import getpass
from typing import Any, Coroutine, List, Set, Tuple


from tqdm import tqdm

from dracoon import DRACOON
from dracoon.client import OAuth2ConnectionType
from dracoon.errors import DRACOONHttpError, HTTPNotFoundError, InvalidArgumentError
from dracoon.nodes.models import Node, NodeItem, NodeType
from dracoon.nodes.responses import NodeList



base_url = 'https://demo.dracoon.com'
client_id = 'XXXXXXXXXXXXXXXXXXXXXXXXX'
client_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXX'

class PathItem:
    """object representing a container node (folder / room) with all required path elements"""
    def __init__(self, dir_path: str):
        self.path = dir_path
        self.parent_path = ("/").join(self.path.split("/")[:-1])
        self.level = len(self.path.split("/")) - 1
    
    def __str__(self) -> str:
        return f"PathItem(path: {self.path} parent:{self.parent_path} level:{self.level})"
    

class PathList:
    """
    List of folders within a room (subrooms excluded) 
    Used to create a tree structure for full node list 
    Provide a node list for any given desired depth 
    as returned from DRACOON nodes APIs (e.g. search)
    """
    def __init__(self, node_list: NodeList, node: Node):
        self.node_list = node_list
        self.node = node
        print(self.base_level)
    
    def get_level(self, level: int) -> List[PathItem]:
        """get all directories in a depth level"""
        level_list = [dir for dir in self.node_items if dir.level == level]
        level_list.sort(key=lambda dir: dir.path)
        return level_list

    def get_by_parent(self, parent: str):
        """get all directories by parent"""
        return [dir for dir in self.node_items if dir.parent_path == parent]

    def get_batches(self, level: int) -> List[List[PathItem]]:
        """create batches based on depth levels"""
        parent_list = set([dir.parent_path for dir in self.get_level(level=level)])

        return [self.get_by_parent(parent) for parent in parent_list]

    @property
    def folder_paths(self) -> list[str]:
        """ returns all folder paths in alphabetical order """
        return sorted([f"{node.parentPath}{node.name}" for node in self.node_list.items])

    @property
    def node_items(self) -> list[PathItem]:
        """ returns node items including level """
        return [PathItem(dir_path=dir_path) for dir_path in self.folder_paths]

    @property
    def levels(self) -> Set[int]:
        """ returns levels """ 
        return set([dir.level for dir in self.node_items])

    @property
    def base_level(self):
        """ return base level of the source container """
        path_comp = self.node.parentPath.split("/")

        if len(path_comp) == 2:
            return 0
        elif len(path_comp) >= 3:
            return len(path_comp) - 2

    def normalize_parent_path(self, parent_path: str, level: int):
        """ remove parent path components if root on specific level """
        path_comp = parent_path.split('/')
        normalized_comp = path_comp[level+1:]
        return "/" + "/".join(normalized_comp)

class DRACOONFolderToRoomConverter:
    """ 
    Converter to convert folders into rooms 
    Creates rooms, moves the content and 
    finally deletes the folder.
    
    Usage: 
    
    converter DRACOONFolderToRoomConverter(dracoon_url=https://your.url)
    converter.connect(username, password)
    converter.convert_to_rooms(path) - for a single level
    """

    
    def __init__(self, dracoon_url: str):
        self.dracoon = DRACOON(base_url=dracoon_url, log_file_out=True, raise_on_err=True)
        
    async def connect(self, username: str, password: str):
        """ connect via password flow to DRACOON """
        try:
            await self.dracoon.connect(OAuth2ConnectionType.password_flow, username=username, password=password)
        except DRACOONHttpError:
            self.dracoon.logger.error("Authentication error")
            raise
        
    def get_rename_room_req(self, room_id: int, name: str) -> Coroutine[Any, Any, Node]:
        """ returns a request for room renaming (awaitable coroutine) """
        payload = self.dracoon.nodes.make_room_update(name=name)
        
        return self.dracoon.nodes.update_room(node_id=room_id, room_update=payload)

    def get_create_room_req(self, parent_id: int, name: str) -> Coroutine[Any, Any, Node]:
        """ returns a request for room creation (awaitable coroutine) """
        payload = self.dracoon.nodes.make_room(parent_id=parent_id, name=name, inherit_perms=True)
    
        return self.dracoon.nodes.create_room(room=payload)
    
    async def get_nodes(self, node_id: int, type: str = 'folder', depth_level: int = 0) -> NodeList:
        """ get a list of nodes by type and depth level (default folder and no depth) """
        nodes = await self.dracoon.nodes.search_nodes(search='*', parent_id=node_id, depth_level=depth_level, filter=f'type:eq:{type}')
        
        if nodes.range.total > 500:
            reqs = [self.dracoon.nodes.search_nodes(search='*', parent_id=node_id, depth_level=depth_level, 
                                                    offset=offset, filter=f'type:eq:{type}') 
                    for offset in range(500, nodes.range.total, 500)]
            
            for batch in self.dracoon.batch_process(coro_list=reqs, batch_size=3):
                responses = await asyncio.gather(*batch)
                for response in responses:
                    nodes.items.extend(*response.items)
                    
        return nodes
                    
    async def move_content(self, target_id: int, node_ids: List[int]):
        """ move a list of node ids to a target in batches of 500 """
        # move in batches of 500 nodes
        for batch in self.dracoon.batch_process(coro_list=node_ids, batch_size=100):
        
            node_list = [NodeItem(id=id) for id in batch]
            transfer = self.dracoon.nodes.make_node_transfer(items=node_list)
            
            await self.dracoon.nodes.move_nodes(target_id=target_id, move_node=transfer)

    async def delete_folders(self, folders: NodeList):
        """ delete a list of node (folder) ids """
        folder_ids = [folder.id for folder in folders.items]
        
        await self.dracoon.nodes.delete_nodes(node_list=folder_ids)
        
    async def get_node_from_path(self, path: str, room_only: bool = False) -> Node:
        """ return node info for a path (e.g. /my_room/myfolder) """
        
        # get node info for a path
        node_info = await self.dracoon.nodes.get_node_from_path(path=path)
        
        if not node_info:
            raise InvalidArgumentError(f"Node with path {path} not found")
        
        if room_only and node_info.type != NodeType.room:
            raise InvalidArgumentError(f"Node with path {path} is not a room ({node_info.type})")
        
        return node_info
        
    async def convert_to_rooms(self, path: str):
        """ convert a given path (level) to rooms """
        # get node from path
        node_info = await self.get_node_from_path(path=path, room_only=True)
        
        # get all folders on level
        folders = await self.get_nodes(node_id=node_info.id)
        
        # create all requests for room creation (rooms are created with name §foldername_room)
        room_reqs = [self.get_create_room_req(parent_id=node_info.id, name=f"{folder.name}_room") for folder in folders.items]
        
        # batch process requests
        for batch in self.dracoon.batch_process(coro_list=room_reqs, batch_size=3):
            responses: List[Node] = await asyncio.gather(*batch)
        
            for folder in folders.items:
                for room in responses:
                    if f"{folder.name}_room" == room.name:
                        try:
                            nodes = await self.get_nodes(node_id=folder.id, type='folder:file')
                        except HTTPNotFoundError:
                            # continue if no files in container
                            continue
                        
                        node_ids = [node.id for node in nodes.items]
                        await self.move_content(target_id=room.id, node_ids=node_ids)
    
        if len(folders.items) > 0:
            await self.delete_folders(folders=folders)
        
        # create all rename requests (rename from $foldername_room to $foldername)
        rooms = await self.get_nodes(node_id=node_info.id, type='room')
        rooms.items = [room for room in rooms.items if room.name[-5:] == '_room']
        room_rename_reqs = [self.get_rename_room_req(room_id=room.id, name=room.name[:-5]) for room in rooms.items]
                     
        # process in batches of 3
        for batch in self.dracoon.batch_process(coro_list=room_rename_reqs, batch_size=3):
            await asyncio.gather(*batch)
            
# parse CLI arguments 
def parse_arguments() -> Tuple[str, int]:
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--path", required=True, help="Path to root room containing folders to convert")
    ap.add_argument("-d", "--depth", required=False, help="Depth level", default=-1)

    args = vars(ap.parse_args())

    # if no path is given, exit
    if args["path"] is None:
        print("Providing a path is mandatory.")
        sys.exit(1)
        
    path = args['path']
    depth_level = args['depth']

    try:
        depth_level = int(depth_level)
    except ValueError:
        print("Depth level must be a valid number.")
        sys.exit(1)
    
    if depth_level is None or depth_level < -1:
        depth_level = -1
   
    return path, depth_level
            

async def main():
    """ main function to convert all folders to rooms recursively """
    
    path, depth_level = parse_arguments()
    
    username = input("Please enter DRACOON username: ")
    password = getpass("Please enter DRACOON password: ")
    
    # connect to DRACOON
    converter = DRACOONFolderToRoomConverter(dracoon_url=base_url)
    await converter.connect(username=username, password=password)
    
    node_info = await converter.get_node_from_path(path=path)
    
    # get all folders in tree
    folders = await converter.get_nodes(node_id=node_info.id, depth_level=depth_level)
    
    # get all paths from folders
    path_list = PathList(node=node_info, node_list=folders)
    
    # start with top level
    await converter.convert_to_rooms(path=path)
    
    # only go into sub folders if explicitly specified
    if depth_level > 0:
        # iterate over all sub levels
        progress = tqdm(unit='folder level', total=len(path_list.levels), unit_scale=True)
        for level in path_list.levels:
            
            for batch in path_list.get_batches(level=level):
                for folder in batch:
                    await converter.convert_to_rooms(path=folder.path)

            progress.update()

        progress.close()

if __name__ == '__main__':
    asyncio.run(main())
    
    

    
    
    
    