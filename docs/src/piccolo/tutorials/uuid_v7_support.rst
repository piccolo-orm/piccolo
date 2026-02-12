UUID v7 support
===============

With Postgres 18 and above, UUID v7 is natively supported.

For this to work in older versions of Postgres a function has to be registered
in the database.

.. note:: CockroachDB does not currently support UUID v7.

You can find many such scripts online. Here's
`one such example <https://github.com/dverite/postgres-uuidv7-sql/blob/396a44433e6e0eb63b1d9d1517e9098256d97351/sql/uuidv7-sql--1.0.sql#L6-L19>`_,
copied below for convenience:

.. code-block:: postgres

    /* Main function to generate a uuidv7 value with millisecond precision */
    CREATE FUNCTION uuidv7(timestamptz DEFAULT clock_timestamp()) RETURNS uuid
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
    $$ LANGUAGE sql volatile parallel safe;

Simply paste this into ``psql``, or any other means of executing SQL on your
database.
