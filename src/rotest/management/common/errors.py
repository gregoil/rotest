"""Define all the resource manager errors."""
# pylint: disable=redefined-outer-name
from future.builtins import str, object


class ServerError(Exception):
    """Hold resource related errors.

    Attributes:
        ERROR_CODE (number): a unique identifier to ServerError type.
            generated automatically.
    """
    ERROR_CODE = None

    def get_error_content(self):
        """Return the error content"""
        return str(self)


class ResourceTypeError(ServerError):
    """Resource type error."""


class ResourceBuildError(ServerError):
    """Resource building error."""


class ResourceReleaseError(ServerError):
    """Resource release error.

    Attributes:
        errors (dict): map a resource name to a tuple containing error code and
            error content. 'res_name' -> ('error_code', content).
    """

    def __init__(self, errors):
        """Build the error according to the given errors.

        Args:
            errors (dict): map a resource name to a tuple containing error code
                and error content. 'res_name' -> ('error_code', content).
        """
        error_message = "Error occurred while trying to release " \
                        "some of the resources: %r" % errors
        super(ResourceReleaseError, self).__init__(error_message)
        self.errors = errors

    def get_error_content(self):
        """Return the error content"""
        return self.errors


class ResourcePermissionError(ServerError):
    """Resource permission error."""


class ResourceUnavailableError(ServerError):
    """Resource unavailable error."""


class ResourceDoesNotExistError(ServerError):
    """Resource does not exist error."""


class ResourceAlreadyAvailableError(ServerError):
    """Resource already available error."""


class UnknownUserError(ServerError):
    """Unknown user has tried to lock a resource."""


class ErrorFactory(object):
    """A factory for build an error from the code and type.

    Attributes:
        CODE_TO_TYPE (dict): holds the connections between error codes and
            error types.
        SUPPORTED_ERRORS (list): holds the errors types.
    """
    CODE_TO_TYPE = {}
    SUPPORTED_ERRORS = [ServerError,
                        UnknownUserError,
                        ResourceTypeError,
                        ResourceBuildError,
                        ResourceReleaseError,
                        ResourcePermissionError,
                        ResourceUnavailableError,
                        ResourceDoesNotExistError,
                        ResourceAlreadyAvailableError]

    for error_type in SUPPORTED_ERRORS:
        error_type.ERROR_CODE = error_type.__name__
        CODE_TO_TYPE[error_type.ERROR_CODE] = error_type

    @classmethod
    def build_error(cls, code, content):
        """Build a ServerError using the given code and fill it with content.

        Args:
            code (number): the error code.
            content (object): the error content.

        Returns:
            ServerError. an error instance.
        """
        error_type = cls.CODE_TO_TYPE[code]

        return error_type(content)
