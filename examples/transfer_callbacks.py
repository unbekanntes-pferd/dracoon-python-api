"""
Example showing how to use the TransferJob class and the callback function to display
up and download progress using smallest intervalls

22.06.2022 Octavio Simone

"""

import logging
import asyncio
from tqdm import tqdm

import dotenv 

from dracoon import DRACOON
from dracoon.client import OAuth2ConnectionType
from dracoon.nodes.models import TransferJob as BaseTransferJob

dotenv.load_dotenv()

base_url = 'https://dracoon.team'
client_id = 'xxxxxxxxxxxxxxxxxxx'
client_secret = 'xxxxxxxxxxxxxxxxxxx'
username = 'xxxxxxxxxxxxxxxxxxx'
password = 'xxxxxxxxxxxxxxxxxxx'
upload_target = '/target/path'
upload_file_small = '/source/path/secret.mp4'


class TransferJob(BaseTransferJob):
    """ object representing a single transfer (up- / download) """
    progress_bar = None
    
    def __init__(self) -> None:
        super().__init__()
    
    def update_progress(self, val: int, total: int = None) -> None:
        self.transferred += val
        if total is not None and self.total == 0:
            self.total = total
            self.progress_bar = tqdm(unit='iMB',unit_divisor=1024, total=self.total, unit_scale=True)
        
        if self.progress_bar:
            self.progress_bar.update(val)
    
    def __del__(self):
        if self.progress_bar:
            self.progress_bar.close()
            
        
    @property
    def progress(self):
        if self.total > 0:
            return self.transferred / self.total
        else:
            return 0

async def main():

    dracoon = DRACOON(base_url=base_url, client_id=client_id, client_secret=client_secret, log_level=logging.INFO)

    await dracoon.connect(connection_type=OAuth2ConnectionType.password_flow, username=username, password=password)
            
    transfer_job = TransferJob()
    # upload in chunks processing min chunks size 5 MB 
    file_small = await dracoon.upload(target_path=upload_target, file_path=upload_file_small, callback_fn=transfer_job.update_progress, 
                                      chunksize=5242880)
    transfer_job = TransferJob()
    # download stream processing 1024 bytes as progress
    await dracoon.download(target_path='./', source_node_id=file_small.node.id, callback_fn=transfer_job.update_progress, chunksize=1024)
        

if __name__ == '__main__':
    asyncio.run(main())