from ..base import Query
from ..mixins import LimitMixin, OrderByMixin, WhereMixin, Output
from .select import Select


class Objects(
    Query,
    LimitMixin,
    OrderByMixin,
    WhereMixin,
):
    """
    Almost identical to select, except you have to select all fields, and
    table instances are returned, rather than just data.
    """

    _output = Output(as_objects=True)

    def __str__(self):
        """
        Need to do this without repeating select ...
        """
        select = Select(
            table=self.table,
            column_names=[]
        )

        for attr in ('_limit', '_where', '_output', 'order_by'):
            setattr(select, attr, getattr(self, attr))

        return select.__str__()
