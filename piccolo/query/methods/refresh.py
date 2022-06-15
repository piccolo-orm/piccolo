from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns import Column
    from piccolo.table import Table


@dataclass
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

    """

    instance: Table
    columns: t.Optional[t.Sequence[Column]] = None

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

    async def run(self) -> Table:
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

        updated_values = (
            await instance.select(*columns)
            .where(pk_column == primary_key_value)
            .first()
        )

        if updated_values is None:
            raise ValueError(
                "The object doesn't exist in the database any more."
            )

        for key, value in updated_values.items():
            setattr(instance, key, value)

        return instance

    def __await__(self):
        """
        If the user doesn't explicity call :meth:`run`, proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def run_sync(self) -> Table:
        """
        Run it synchronously. For example::

            my_instance.refresh().run_sync()

        """
        return run_sync(self.run())
