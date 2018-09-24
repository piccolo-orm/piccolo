from ..base import Query


class Raw(Query):

    def __str__(self):
        return self.base
