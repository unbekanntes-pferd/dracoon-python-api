# ---------------------------------------------------------------------------#
# Python module to provide DRACOON api calls for file upload
# Requires Dracoon call handlers 
# Version 0.1.0
# Author: Octavio Simone, 30.10.2020
# Part of dracoon Python package
# ---------------------------------------------------------------------------#



# collection of DRACOON API calls for file upload
# documentation: https://dracoon.team/api/swagger-ui/index.html?configUrl=/api/spec_v4/swagger-config#/uploads 
# Please note: maximum 500 items are returned in GET requests 
# - refer to documentation on how to upload files:
# https://support.dracoon.com/hc/de/articles/115005512089

from .uploads_models import FinalizeUpload
from pydantic import validate_arguments, HttpUrl

# upload a file (step 2 of file upload process - to generate an upload url, use nodes.create_upload_channel)
@validate_arguments
def upload_file(uploadURL: HttpUrl, upload_file, contentRange: int = None):
    api_call = {
        'url': uploadURL,
        'files': upload_file,
        'method': 'POST'
    }
    if contentRange != None: api_call["Content-Range"] = contentRange
    return api_call

# finalie upload - body/params must be empty for public
@validate_arguments
def finalize_upload(uploadURL: HttpUrl, params: FinalizeUpload=None):
    api_call = {
        'url': uploadURL,
        'files': None,
        'method': 'PUT',
        'content_type': 'application/json'
    }
    if params != None: api_call["body"] = params

    return api_call

# delete upload request
@validate_arguments
def cancel_upload(uploadURL: HttpUrl):
    api_call = {
        'url': uploadURL,
        'files': None,
        'method': 'DELETE',
        'content_type': 'application/json'
    }
    return api_call