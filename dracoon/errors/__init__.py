from httpx import HTTPStatusError

class FileKeyEncryptionError(Exception):
    """
    Exception raised in dracoon.crypto
    File key could not be encrypted

    """

    def __init__(self, message: str = "File key could not be encrypted"):

        self.message = message

        super().__init__(self.message)


class InvalidKeypairVersionError(Exception):
    """
    Exception raised in dracoon.crypto
    Invalid keypair version
    Valid keypair versions: UserKeypairVersion

    """

    def __init__(self, message: str = "Invalid keypair version"):

        self.message = message

        super().__init__(self.message)

class InvalidFileKeyError(Exception):
    """
    Exception raised in dracoon.crypto
    Invalid file key
    File key needs to have correct version, key and iv

    """

    def __init__(self, message: str = "Invalid file key"):

        self.message = message

        super().__init__(self.message)

class CryptoMissingDataError(Exception):
    """
    Exception raised in dracoon.crypto
    Missing data to process
    No content (bytes) provided
    """

    def __init__(self, message: str = "No data to process."):

        self.message = message

        super().__init__(self.message)

class CryptoMissingKeypairError(Exception):
    """
    Exception raised in dracoon
    Missing keypair unlock
    Keypair must be obtained for crypto nodes
    """

    def __init__(self, message: str = "Missing keypair."):

        self.message = message

        super().__init__(self.message)


class MissingCredentialsError(Exception):
    """
    Exception raised in dracoon.client
    Missing credentials for flow
    Password flow requires username and password
    Authorization code required auth code
    Refresh token requires refresh token
    """

    def __init__(self, message: str = "Missing credentials for OAuth2 flow."):

        self.message = message

        super().__init__(self.message)

class ClientDisconnectedError(Exception):
    """
    Exception raised in dracoon modules
    Client is not connected (client.connect())
    """

    def __init__(self, message: str = "Client must be connected (client.connect())."):

        self.message = message

        super().__init__(self.message)

class InvalidClientError(Exception):
    """
    Exception raised in dracoon modules
    Client does not adhere to format (DRACOONClient)
    """

    def __init__(self, message: str = "Invalid client."):

        self.message = message

        super().__init__(self.message)


class InvalidArgumentError(Exception):
    """
    Exception raised in dracoon modules
    Value provided not valid 
    Examples: EULA acceptance cannot be undone
    """

    def __init__(self, message: str = "Invalid argument."):

        self.message = message

        super().__init__(self.message)

class InvalidFileError(Exception):
    """
    Exception raised in dracoon.uploads
    File with given path not found.
    """

    def __init__(self, message: str = "File not found."):

        self.message = message

        super().__init__(self.message)


class FileConflictError(Exception):
    """
    Exception raised in dracoon.nodes
    File to download exists on target path (name)
    """

    def __init__(self, message: str = "File already exists."):

        self.message = message

        super().__init__(self.message)

class InvalidPathError(Exception):
    """
    Exception raised in dracoon.nodes
    Path provided is not a folder.
    """

    def __init__(self, message: str = "Path is not a folder."):

        self.message = message

        super().__init__(self.message)


class DRACOONClientError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code >= 400)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON API error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.message)

    def __str__(self):
        if not self.is_xml:
            return f"{self.error.response.text}"
        else:
            return f"{self.error.response.content}"


class HTTPBadRequestError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 400)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Bad Request Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPUnauthorizedError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 401)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Unauthorized Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.message)

    def __str__(self):

        return f"{self.error.response.text}"

        # if not is_xml:
        #     return f"{self.error.response.text}"
        # else:
        #     return f"{self.error.response.content}"


class HTTPPaymentRequiredError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 402)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Payment Required Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPForbiddenError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 403)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Forbidden Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPNotFoundError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 404)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Not Found Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPConflictError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 409)

    """
    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Conflict Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPPreconditionsFailedError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 412)

    """

    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON Precondition Failed Error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)


class HTTPUnknownError(Exception):
    """
    Exception raised for errors returned by DRACOON API 
    (status code 500 or not covered by other errors above)

    """

    def __init__(self, error: HTTPStatusError, is_xml: bool = False, message: str = "DRACOON unknown error"):
        
        # required for AWS S3 XML responses
        self.is_xml = is_xml
        self.error = error
        self.message = message

        super().__init__(self.error, self.is_xml, self.message)









