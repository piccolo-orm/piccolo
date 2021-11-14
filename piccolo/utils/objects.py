from __future__ import annotations

import typing as t

from piccolo.columns.column_types import ForeignKey

if t.TYPE_CHECKING:
    from piccolo.table import Table


def make_nested_object(
    row: t.Dict[str, t.Any], table_class: t.Type[Table]
) -> Table:
    """
    Takes a nested dictionary such as this:

    .. code-block:: python

        row = {
            'id': 1,
            'name': 'Pythonistas',
            'manager': {'id': 1, 'name': 'Guido'}
        }

    And returns a ``Table`` instance, with nested table instances for related
    tables.

    For example:

    .. code-block:: python

        band = make_nested(row, Band)
        >>> band
        <Band: 1>
        >>> band.manager
        <Manager: 1>
        >>> band.manager.id
        1

    """
    table_params: t.Dict[str, t.Any] = {}

    for key, value in row.items():
        if isinstance(value, dict):
            # This is probably a related table.
            fk_column = table_class._meta.get_column_by_name(key)

            if isinstance(fk_column, ForeignKey):
                related_table_class = (
                    fk_column._foreign_key_meta.resolved_references
                )
                table_params[key] = make_nested_object(
                    value, related_table_class
                )
            else:
                # The value doesn't belong to a foreign key, so just append it.
                table_params[key] = value

        else:
            table_params[key] = value

    table_instance = table_class(**table_params)
    table_instance._exists_in_db = True
    return table_instance
