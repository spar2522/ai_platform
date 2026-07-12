class CanonicaError(Exception):
    """Base exception class for all Canonica-related errors.

    This class serves as the foundation for all exceptions raised by the Canonica
    package. It is intended to be used as a base class for more specific exceptions
    that may occur during document processing, interpretation, or other operations.
    """


class NoInterpreterFoundError(CanonicaError):
    """Raised when no interpreter is found for a given document.

    This exception is raised when a document is encountered that cannot be
    interpreted by any available interpreter in the system. It typically occurs
    during document loading or processing when the format is unrecognized.
    """