from __future__ import annotations

import typing as t

try:
    import orjson

    ORJSON = True
except ImportError:
    import json

    ORJSON = False


def dump_json(data: t.Any, pretty=False) -> str:
    if ORJSON:
        if pretty:
            return orjson.dumps(
                data,
                default=str,
                option=(
                    orjson.OPT_INDENT_2
                    | orjson.OPT_APPEND_NEWLINE  # type: ignore
                ),
            ).decode("utf8")
        else:
            return orjson.dumps(data, default=str).decode("utf8")
    else:
        if pretty:
            return json.dumps(data, default=str, indent=2)
        else:
            return json.dumps(data, default=str)


def load_json(data: str) -> t.Any:
    if ORJSON:
        return orjson.loads(data)
    else:
        return json.loads(data)
