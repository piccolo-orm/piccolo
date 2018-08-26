class Operator():
    pass


class Equal(Operator):
    template = '{name} = {value}'


class NotEqual(Operator):
    template = '{name} != {value}'


class In(Operator):
    template = '{name} IN ({values})'


class NotIn(Operator):
    template = '{name} NOT IN ({values})'


class Like(Operator):
    template = '{name} LIKE {value}'
