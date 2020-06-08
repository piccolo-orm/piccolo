from .base import Operator


class MathOperator(Operator):
    pass


class Add(MathOperator):
    template = "{name} + {value}"


class Subtract(MathOperator):
    template = "{name} - {value}"


class Multiply(MathOperator):
    template = "{name} * {value}"


class Divide(MathOperator):
    template = "{name} * {value}"
