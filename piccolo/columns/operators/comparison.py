from .base import Operator


class ComparisonOperator(Operator):
    template = ""


class IsNull(ComparisonOperator):
    template = "{name} IS NULL"


class Equal(ComparisonOperator):
    template = "{name} = {value}"


class NotEqual(ComparisonOperator):
    template = "{name} != {value}"


class In(ComparisonOperator):
    template = "{name} IN ({values})"


class NotIn(ComparisonOperator):
    template = "{name} NOT IN ({values})"


class Like(ComparisonOperator):
    template = "{name} LIKE {value}"


class ILike(ComparisonOperator):
    template = "{name} ILIKE {value}"


class NotLike(ComparisonOperator):
    template = "{name} NOT LIKE {value}"


class GreaterThan(ComparisonOperator):
    # Add permitted types???
    template = "{name} > {value}"


class GreaterEqualThan(ComparisonOperator):
    template = "{name} >= {value}"


class LessThan(ComparisonOperator):
    template = "{name} < {value}"


class LessEqualThan(ComparisonOperator):
    template = "{name} <= {value}"
