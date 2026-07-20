from __future__ import annotations

from typing import TYPE_CHECKING

from piccolo.engine.exceptions import ExtensionNotInstalled
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from piccolo.columns import Column
    from piccolo.columns.indexes import IndexMethod
    from piccolo.engine.base import Engine


async def check_extensions_for_create(
    engine: Engine, columns: list[Column]
) -> None:
    if engine.engine_type != "postgres":
        return
    needed = {
        ext
        for col in columns
        if (ext := getattr(col, "required_extension", None))
    }
    await _assert_extensions_installed(engine, needed)


async def check_extensions_for_index(
    engine: Engine,
    method: IndexMethod,
    operator_class: str | None,
) -> None:
    if engine.engine_type != "postgres":
        return
    from piccolo.columns.indexes import IndexMethod as IM

    needed: set[str] = set()
    if method in (IM.hnsw, IM.ivfflat):
        needed.add("vector")
    if operator_class and "trgm" in operator_class:
        needed.add("pg_trgm")
    await _assert_extensions_installed(engine, needed)


def _encode_vector(v: object) -> str:
    parts = ",".join(str(x) for x in v)  # type: ignore[attr-defined]
    return f"[{parts}]"


def _decode_vector(s: str) -> list:
    return [float(x) for x in s.strip("[]").split(",")]


async def register_codecs(conn: object) -> None:
    """Register asyncpg codecs for PostgreSQL extension types."""
    try:
        await conn.set_type_codec(  # type: ignore[attr-defined]
            "vector",
            encoder=_encode_vector,
            decoder=_decode_vector,
            schema="public",
            format="text",
        )
    except ValueError as e:
        if "unknown type" not in str(e):
            raise


async def _assert_extensions_installed(
    engine: Engine, extension_names: set[str]
) -> None:
    for ext in extension_names:
        result = await engine.run_querystring(
            QueryString(
                "SELECT 1 FROM pg_extension WHERE extname = {}",
                ext,
            )
        )
        if not result:
            raise ExtensionNotInstalled(
                f"The '{ext}' PostgreSQL extension is required but not "
                f'installed. Run: CREATE EXTENSION "{ext}";'
            )
