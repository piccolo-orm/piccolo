class TransactionError(Exception):
    pass


###############################################################################
# These are generic database Exceptions as specified in PEP 249:
# https://peps.python.org/pep-0249/#exceptions


class Error(Exception):
    pass


class InterfaceError(Error):
    pass


class DatabaseError(Error):
    pass


class DataError(DatabaseError):
    pass


class OperationalError(DatabaseError):
    pass


class IntegrityError(DatabaseError):
    pass


class InternalError(DatabaseError):
    pass


class ProgrammingError(DatabaseError):
    pass


class NotSupportedError(DatabaseError):
    pass


# TODO - write async context manager which maps these exceptions to generic
# exceptions:
# https://github.com/MagicStack/asyncpg/blob/master/asyncpg/exceptions/__init__.py
