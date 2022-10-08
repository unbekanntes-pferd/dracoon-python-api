from httpx import HTTPStatusError


class DRACOONBaseError(Exception):
    """
    Base exception for all errors

    """

    def __init__(self, message: str):

        super().__init__(message)
        self.message = message

class DRACOONCryptoError(DRACOONBaseError):
    """
    Base exception for crypto related errors

    """

    def __init__(self, message: str):

        super().__init__(message)
  
class DRACOONClientError(DRACOONBaseError):
    """
    Base exception for client related errors

    """

    def __init__(self, message: str):

        super().__init__(message)

       
class DRACOONValidationError(DRACOONBaseError):
    """
    Base exception for validation related errors

    """

    def __init__(self, message: str):

        super().__init__(message)


class FileKeyEncryptionError(DRACOONCryptoError):
    """
    Exception raised in dracoon.crypto
    File key could not be encrypted

    """

    def __init__(self, message: str = "File key could not be encrypted"):

        super().__init__(message)



class InvalidKeypairVersionError(DRACOONCryptoError):
    """
    Exception raised in dracoon.crypto
    Invalid keypair version
    Valid keypair versions: UserKeypairVersion

    """

    def __init__(self, message: str = "Invalid keypair version"):

        super().__init__(message)

class InvalidFileKeyError(DRACOONCryptoError):
    """
    Exception raised in dracoon.crypto
    Invalid file key
    File key needs to have correct version, key and iv

    """

    def __init__(self, message: str = "Invalid file key"):

        super().__init__(message)

class CryptoMissingDataError(DRACOONCryptoError):
    """
    Exception raised in dracoon.crypto
    Missing data to process
    No content (bytes) provided
    """

    def __init__(self, message: str = "No data to process."):

        super().__init__(message)

class CryptoMissingKeypairError(DRACOONCryptoError):
    """
    Exception raised in dracoon
    Missing keypair unlock
    Keypair must be obtained for crypto nodes
    """

    def __init__(self, message: str = "Missing keypair."):

        super().__init__(message)
        
class CryptoMissingFileKeyError(DRACOONCryptoError):
    """
    Exception raised in dracoon
    Missing file key for user and node
    """

    def __init__(self, message: str = "Missing file key."):

        super().__init__(message)


class MissingCredentialsError(DRACOONClientError):
    """
    Exception raised in dracoon.client
    Missing credentials for flow
    Password flow requires username and password
    Authorization code required auth code
    Refresh token requires refresh token
    """

    def __init__(self, message: str = "Missing credentials for OAuth2 flow."):

        super().__init__(message)

class ClientDisconnectedError(DRACOONClientError):
    """
    Exception raised in dracoon modules
    Client is not connected (client.connect())
    """

    def __init__(self, message: str = "Client must be connected (client.connect())."):

        super().__init__(message)

class InvalidClientError(DRACOONClientError):
    """
    Exception raised in dracoon modules
    Client does not adhere to format (DRACOONClient)
    """

    def __init__(self, message: str = "Invalid client."):

        super().__init__(message)


class InvalidArgumentError(DRACOONValidationError):
    """
    Exception raised in dracoon modules
    Value provided not valid 
    Examples: EULA acceptance cannot be undone
    """

    def __init__(self, message: str = "Invalid argument."):

        super().__init__(message)

class InvalidFileError(DRACOONValidationError):
    """
    Exception raised in dracoon.uploads
    File with given path not found.
    """

    def __init__(self, message: str = "File not found."):

        super().__init__(message)


class FileConflictError(DRACOONValidationError):
    """
    Exception raised in dracoon.nodes
    File to download exists on target path (name)
    """

    def __init__(self, message: str = "File already exists."):

        super().__init__(message)

class InvalidPathError(DRACOONValidationError):
    """
    Exception raised in dracoon.nodes
    Path provided is not a folder.
    """

    def __init__(self, message: str = "Path is not a folder."):

        super().__init__(message)


class DRACOONHttpError(DRACOONBaseError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code >= 400)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON API error"):
        
        super().__init__(message)
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        

class HTTPBadRequestError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 400)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Bad Request Error"):
        
        super().__init__(error, is_xml, message)


class HTTPUnauthorizedError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 401)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Unauthorized Error"):
        
        super().__init__(error, is_xml, message)

class HTTPPaymentRequiredError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 402)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Payment Required Error"):
        
        super().__init__(error, is_xml, message)


class HTTPForbiddenError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 403)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Forbidden Error"):
        
        
        super().__init__(error, is_xml, message)


class HTTPNotFoundError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 404)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Not Found Error"):
        
        
        super().__init__(error, is_xml, message)


class HTTPConflictError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 409)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Conflict Error"):
        
        
        super().__init__(error, is_xml, message)


class HTTPPreconditionsFailedError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 412)

    """

    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Precondition Failed Error"):
        
        
        super().__init__(error, is_xml, message)


class HTTPUnknownError(DRACOONHttpError):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 500 or not covered by other errors above)

    """

    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON unknown error"):
        
        
        super().__init__(error, is_xml, message)









