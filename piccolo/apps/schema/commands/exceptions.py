class SchemaCommandError(Exception):
    """
    Base class for all schema command errors.
    """

    pass


class GenerateError(SchemaCommandError):
    """
    Raised when an error occurs during schema generation.
    """

    pass
