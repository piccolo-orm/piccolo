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

`MySQL <https://www.mysql.com/>`_ has limited support due to some MySQL limitations.
MySQL does not have the specific column types (such as ``Array``, proper ``UUID`` support etc.) 
and features that Postgres offers out of the box. MySQL does not have a ``RETURNING`` 
clause which disables support for specifying a custom primary key column 
(such as ``UUID`` or ``Varchar``). The main missing feature is support for
:ref:`automatic database migrations <AutoMigrations>` because MySQL ``DDL`` 
statements `is not transactional <https://dev.mysql.com/doc/refman/8.4/en/atomic-ddl.html>`_ 
and MySQL will commit the changes immediately in transaction and it is not 
possible to roll back the migration steps. To prevent this behavior, we need 
to use manual migrations with transactions disabled 
(by default all Piccolo migrations are automatically wrapped in a transaction).
We can achieve this by setting the ``MigrationManager`` argument ``wrap_in_transaction`` 
to ``False`` so that the migration is not wrapped in a transaction.

What about other databases?
---------------------------

Our focus is on providing great support for a limited number of databases
(especially Postgres), however it's likely that we'll support more databases in
the future.
