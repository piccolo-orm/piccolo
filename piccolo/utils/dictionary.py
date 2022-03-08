from __future__ import annotations

import typing as t


def make_nested(dictionary: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Rows are returned from the database as a flat dictionary, with keys such
    as ``'manager.name'`` if the column belongs to a related table.

    This function puts any values from a related table into a sub dictionary.

    .. code-block:: python

        response = await Band.select(Band.name, Band.manager.name)
        >>> print(response)
        [{'name': 'Pythonistas', 'band.name': 'Guido'}]

        >>> make_nested(response[0])
        {'name': 'Pythonistas', 'band': {'name': 'Guido'}}

    """
    output: t.Dict[str, t.Any] = {}

    items = list(dictionary.items())
    items.sort(key=lambda x: x[0])

    for key, value in items:
        path = key.split(".")
        if len(path) == 1:
            output[path[0]] = value
        else:
            # Force the root element to be an empty dictionary, if it's some
            # other value (most likely an integer). This is because there are
            # situations where a query can have `band` and `band.id`.
            # For example:
            # await Band.select(
            #     Band.all_columns(),
            #     Band.manager.all_columns()
            # ).run()
            # In this situation nesting takes precendence.
            root = output.get(path[0], None)
            if isinstance(root, dict):
                dictionary = root
            else:
                dictionary = {}
                output[path[0]] = dictionary

            for path_element in path[1:-1]:
                root = dictionary.setdefault(path_element, {})
                if not isinstance(root, dict):
                    root = {}
                    dictionary[path_element] = root
                dictionary = root

            dictionary[path[-1]] = value

    return output
