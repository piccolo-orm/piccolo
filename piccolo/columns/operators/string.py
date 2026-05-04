from .base import Operator


class StringOperator(Operator):
    pass


class Concat(StringOperator):
    template = "{value_1} || {value_2}"
