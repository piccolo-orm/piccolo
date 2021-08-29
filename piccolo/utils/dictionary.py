from __future__ import annotations

import typing as t


def make_nested(dictionary: t.Dict[str, t.Any]) -> t.Dict[str, t.Any]:
    """
    Rows are returned from the database as a flat dictionary, with keys such
    as ``'manager.name'`` if the column belongs to a related table.

    This function puts any values from a related table into a sub dictionary.

    .. code-block::

        response = Band.select(Band.name, Band.manager.name).run_sync()
        >>> print(response)
        [{'name': 'Pythonistas', 'band.name': 'Guido'}]

        >>> make_nested(response[0])
        {'name': 'Pythonistas', 'band': {'name': 'Guido'}}

    """
    output: t.Dict[str, t.Any] = {}

    for key, value in dictionary.items():
        path = key.split(".")
        if len(path) == 1:
            output[path[0]] = value
        else:
            dictionary = output.setdefault(path[0], {})
            for path_element in path[1:-1]:
                dictionary = dictionary.setdefault(path_element, {})
            dictionary[path[-1]] = value

    return output
