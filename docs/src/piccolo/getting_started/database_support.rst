.. _DatabaseSupport:

Database Support
================

`Postgres <https://www.postgresql.org/>`_ is the primary database which Piccolo
was designed for. It's robust, feature rich, and a great choice for most projects.

`CockroachDB <https://www.cockroachlabs.com/>`_ is also supported. It's designed
to be scalable and fault tolerant, and is mostly compatible with Postgres.
There may be some minor features not supported, but it's OK to use.

`SQLite <https://www.sqlite.org/index.html>`_ support was originally added to
enable tooling like the :ref:`playground <Playground>`, but over time we've
added more and more support. Many people successfully use SQLite and Piccolo
together in production. The main missing feature is support for
:ref:`automatic database migrations <AutoMigrations>` due to SQLite's limited
support for ``ALTER TABLE`` ``DDL`` statements.

What about other databases?
---------------------------

Our focus is on providing great support for a limited number of databases
(especially Postgres), however it's likely that we'll support more databases in
the future.
