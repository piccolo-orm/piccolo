from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, NamedTuple

from piccolo.engine.exceptions import ExtensionNotInstalled
from piccolo.querystring import QueryString

if TYPE_CHECKING:
    from asyncpg import Connection

    from piccolo.columns import Column
    from piccolo.columns.indexes import IndexMethod
    from piccolo.engine.base import Engine


###############################################################################
# Extension checks, which run before DDL.


async def check_extensions_for_create(
    engine: Engine, columns: list[Column], in_pool: bool = True
) -> None:
    if engine.engine_type != "postgres":
        return
    needed = {
        ext
        for col in columns
        if (ext := getattr(col, "required_extension", None))
    }
    await _assert_extensions_installed(engine, needed, in_pool=in_pool)


async def check_extensions_for_index(
    engine: Engine,
    method: IndexMethod,
    operator_class: str | None,
    in_pool: bool = True,
) -> None:
    if engine.engine_type != "postgres":
        return
    from piccolo.columns.indexes import IndexMethod as IM

    needed: set[str] = set()
    if method in (IM.hnsw, IM.ivfflat):
        needed.add("vector")
    if operator_class and "trgm" in operator_class:
        needed.add("pg_trgm")
    await _assert_extensions_installed(engine, needed, in_pool=in_pool)


async def _assert_extensions_installed(
    engine: Engine, extension_names: set[str], in_pool: bool = True
) -> None:
    if not extension_names:
        return

    response = await engine.run_querystring(
        QueryString(
            "SELECT extname FROM pg_extension WHERE extname = ANY({})",
            sorted(extension_names),
        ),
        in_pool=in_pool,
    )
    installed = {row["extname"] for row in response}

    missing = sorted(extension_names - installed)
    if missing:
        names = ", ".join(f"'{ext}'" for ext in missing)
        statements = " ".join(f'CREATE EXTENSION "{ext}";' for ext in missing)
        raise ExtensionNotInstalled(
            f"The {names} PostgreSQL extension is required but not "
            f"installed. Run: {statements}"
        )


###############################################################################
# asyncpg codecs for extension types.


def _encode_vector(v: object) -> str:
    parts = ",".join(str(x) for x in v)  # type: ignore[attr-defined]
    return f"[{parts}]"


def _decode_vector(s: str) -> list:
    return [float(x) for x in s.strip("[]").split(",")]


class _Codec(NamedTuple):
    type_name: str
    encoder: Callable[[Any], str]
    decoder: Callable[[str], Any]


# Maps an extension name to the codec for the type it adds.
_CODECS: dict[str, _Codec] = {
    "vector": _Codec(
        type_name="vector", encoder=_encode_vector, decoder=_decode_vector
    ),
}

# The extensions which at least one defined column needs. Codecs are only
# registered for these, so apps which don't use them pay no extra cost per
# connection.
_used_extensions: set[str] = set()


def mark_extension_used(extension: str) -> None:
    """
    Called by column types with a ``required_extension`` which also needs an
    asyncpg codec (for example ``Vector``).
    """
    _used_extensions.add(extension)


async def register_codecs(
    conn: Connection, schema_cache: dict[str, str]
) -> None:
    """
    Register asyncpg codecs for PostgreSQL extension types.

    :param schema_cache:
        Maps an extension name to the schema it's installed in. Only positive
        results are cached - if the extension isn't installed yet, we look
        again on the next connection, so an extension created after the pool
        starts gets picked up by new connections.

    If the extension isn't installed, this does nothing.

    """
    for ext in sorted(_used_extensions & _CODECS.keys()):
        schema = schema_cache.get(ext)

        if schema is None:
            schema = await conn.fetchval(
                "SELECT n.nspname FROM pg_extension e "
                "JOIN pg_namespace n ON n.oid = e.extnamespace "
                "WHERE e.extname = $1",
                ext,
            )
            if schema is None:
                continue
            schema_cache[ext] = schema

        codec = _CODECS[ext]

        try:
            await conn.set_type_codec(
                codec.type_name,
                encoder=codec.encoder,
                decoder=codec.decoder,
                schema=schema,
                format="text",
            )
        except ValueError as e:
            # The extension was dropped, or moved to another schema, since we
            # cached it.
            if "unknown type" not in str(e):
                raise
            schema_cache.pop(ext, None)
