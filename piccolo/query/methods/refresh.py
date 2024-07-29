from __future__ import annotations

import typing as t

from piccolo.utils.encoding import JSONDict
from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


class Refresh:
    """
    Used to refresh :class:`Table <piccolo.table.Table>` instances with the
    latest data data from the database. Accessible via
    :meth:`refresh <piccolo.table.Table.refresh>`.

    :param instance:
        The instance to refresh.
    :param columns:
        Which columns to refresh - it not specified, then all columns are
        refreshed.
    :param load_json:
        Whether to load ``JSON`` / ``JSONB`` columns as objects, instead of
        just a string.

    """

    def __init__(
        self,
        instance: Table,
        columns: t.Optional[t.Sequence[Column]] = None,
        load_json: bool = False,
    ):
        self.instance = instance

        if columns:
            for column in columns:
                if len(column._meta.call_chain) > 0:
                    raise ValueError(
                        "We can't currently selectively refresh certain "
                        "columns on child objects (e.g. Concert.band_1.name). "
                        "Please just specify top level columns (e.g. "
                        "Concert.band_1), and the entire child object will be "
                        "refreshed."
                    )

        self.columns = columns
        self.load_json = load_json

    @property
    def _columns(self) -> t.Sequence[Column]:
        """
        Works out which columns the user wants to refresh.
        """
        if self.columns:
            return self.columns

        return [
            i for i in self.instance._meta.columns if not i._meta.primary_key
        ]

    def _get_columns(self, instance: Table, columns: t.Sequence[Column]):
        """
        If `prefetch` was used on the object, for example::

            >>> await Band.objects(Band.manager)

        We should also update the prefetched object.

        It works multiple level deep. If we refresh this::

            >>> await Album.objects(Album.band.manager).first()

        It will update the nested `band` object, and also the `manager`
        object.

        """
        from piccolo.columns.column_types import ForeignKey
        from piccolo.table import Table

        select_columns = []

        for column in columns:
            if isinstance(column, ForeignKey) and isinstance(
                (child_instance := getattr(instance, column._meta.name)),
                Table,
            ):
                select_columns.extend(
                    self._get_columns(
                        child_instance,
                        # Fetch all columns (even the primary key, just in
                        # case the foreign key now references a different row).
                        column.all_columns(),
                    )
                )
            else:
                select_columns.append(column)

        return select_columns

    def _update_instance(self, instance: Table, data_dict: t.Dict):
        """
        Update the table instance. It is called recursively, if the instance
        has child instances.
        """
        for key, value in data_dict.items():
            if isinstance(value, dict) and not isinstance(value, JSONDict):
                # If the value is a dict, then it's a child instance.
                if all(i is None for i in value.values()):
                    # If all values in the nested object are None, then we can
                    # safely assume that the object itself is null, as the
                    # primary key value must be null.
                    setattr(instance, key, None)
                else:
                    self._update_instance(getattr(instance, key), value)
            else:
                setattr(instance, key, value)

    async def run(
        self, in_pool: bool = True, node: t.Optional[str] = None
    ) -> Table:
        """
        Run it asynchronously. For example::

            await my_instance.refresh().run()

            # or for convenience:
            await my_instance.refresh()

        Modifies the instance in place, but also returns it as a convenience.

        """
        instance = self.instance

        if not instance._exists_in_db:
            raise ValueError("The instance doesn't exist in the database.")

        pk_column = instance._meta.primary_key

        primary_key_value = getattr(instance, pk_column._meta.name, None)

        if primary_key_value is None:
            raise ValueError("The instance's primary key value isn't defined.")

        columns = self._columns
        if not columns:
            raise ValueError("No columns to fetch.")

        select_columns = self._get_columns(
            instance=self.instance, columns=columns
        )

        data_dict = (
            await instance.__class__.select(*select_columns)
            .where(pk_column == primary_key_value)
            .output(nested=True, load_json=self.load_json)
            .first()
            .run(node=node, in_pool=in_pool)
        )

        if data_dict is None:
            raise ValueError(
                "The object doesn't exist in the database any more."
            )

        self._update_instance(instance=instance, data_dict=data_dict)

        return instance

    def __await__(self):
        """
        If the user doesn't explicity call :meth:`run`, proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self, *args, **kwargs) -> Table:
        """
        Run it synchronously. For example::

            my_instance.refresh().run_sync()

        """
        return run_sync(self.run(*args, **kwargs))
