from __future__ import annotations

import typing as t

try:
    import orjson

    ORJSON = True
except ImportError:
    import json

    ORJSON = False


def dump_json(data: t.Any, pretty: bool = False) -> str:
    if ORJSON:
        orjson_params: t.Dict[str, t.Any] = {"default": str}
        if pretty:
            orjson_params["option"] = (
                orjson.OPT_INDENT_2 | orjson.OPT_APPEND_NEWLINE  # type: ignore
            )
        return orjson.dumps(data, **orjson_params).decode(  # type: ignore
            "utf8"
        )
    else:
        params: t.Dict[str, t.Any] = {"default": str}
        if pretty:
            params["indent"] = 2
        return json.dumps(data, **params)  # type: ignore


class JSONDict(dict):
    """
    Once we have parsed a JSON string into a dictionary, we can't distinguish
    it from other dictionaries.

    Sometimes we might want to - for example::

        >>> await Album.select(
        ...     Album.all_columns(),
        ...     Album.recording_studio.all_columns()
        ... ).output(
        ...     nested=True,
        ...     load_json=True
        ... )

        [{
            'id': 1,
            'band': 1,
            'name': 'Awesome album 1',
            'recorded_at': {
                'id': 1,
                'facilities': {'restaurant': True, 'mixing_desk': True},
                'name': 'Abbey Road'
            },
            'release_date': datetime.date(2021, 1, 1)
        }]

    Facilities could be mistaken for a table.

    """

    ...


def load_json(data: str) -> t.Any:
    response = (
        orjson.loads(data) if ORJSON else json.loads(data)  # type: ignore
    )

    if isinstance(response, dict):
        return JSONDict(**response)

    return response
