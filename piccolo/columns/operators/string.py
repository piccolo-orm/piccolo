from .base import Operator


class StringOperator(Operator):
    pass


class ConcatPostgres(StringOperator):
    template = "CONCAT({value_1}, {value_2})"


class ConcatSQLite(StringOperator):
    template = "{value_1} || {value_2}"
