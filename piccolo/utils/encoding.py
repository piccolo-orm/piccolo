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
        return orjson.dumps(data, **orjson_params).decode("utf8")
    else:
        params: t.Dict[str, t.Any] = {"default": str}
        if pretty:
            params["indent"] = 2
        return json.dumps(data, **params)


def load_json(data: str) -> t.Any:
    return orjson.loads(data) if ORJSON else json.loads(data)
