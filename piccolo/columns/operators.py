class Operator():
    template = ''


class Equal(Operator):
    template = '{name} = {value}'


class NotEqual(Operator):
    template = '{name} != {value}'


class In(Operator):
    template = '{name} IN ({values})'


class NotIn(Operator):
    template = '{name} NOT IN ({values})'


class Like(Operator):
    template = "{name} LIKE {value}"


class ILike(Operator):
    template = "{name} ILIKE {value}"


class NotLike(Operator):
    template = "{name} NOT LIKE {value}"


class GreaterThan(Operator):
    # Add permitted types???
    template = "{name} > {value}"


class GreaterEqualThan(Operator):
    template = "{name} >= {value}"


class LessThan(Operator):
    template = "{name} < {value}"


class LessEqualThan(Operator):
    template = "{name} <= {value}"
