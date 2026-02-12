from typing import Literal

try:
    from uuid import uuid7  # type: ignore
except ImportError:
    # For version < Python 3.14
    from ._uuid_backport import uuid7


def get_uuid7_db_polyfill(engine_type: Literal["postgres", "cockroach"]):
    parallel_safe = engine_type == "postgres"

    return f"""
    CREATE OR REPLACE FUNCTION uuidv7(
        timestamptz DEFAULT clock_timestamp()
    ) RETURNS uuid
    AS $$
    -- Replace the first 48 bits of a uuidv4 with the current
    -- number of milliseconds since 1970-01-01 UTC
    -- and set the "ver" field to 7 by setting additional bits
    select encode(
        set_bit(
        set_bit(
            overlay(uuid_send(gen_random_uuid()) placing
        substring(int8send((extract(epoch from $1)*1000)::bigint) from 3)
        from 1 for 6),
        52, 1),
        53, 1), 'hex')::uuid;
    $$ LANGUAGE sql volatile {'parallel safe' if parallel_safe else ''};
    """


__all__ = ("uuid7", "get_uuid7_db_polyfill")
