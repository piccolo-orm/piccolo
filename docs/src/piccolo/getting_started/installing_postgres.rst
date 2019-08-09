.. _setting_up_postgres:

Installing Postgres
===================

Mac
---

The quickest way to get Postgres up and running on the Mac is using
`Postgres.app <https://postgresapp.com/>`_.

Ubuntu
------

On Ubuntu you can use `apt <https://help.ubuntu.com/community/PostgreSQL>`_.

Windows
-------

For Windows, you can use a package manager like
`chocolatey <https://chocolatey.org/packages/postgresql>`_.

Postgres version
----------------

Piccolo is currently tested against Postgres 9.6, 10.6, and 11.1 so it's
recommended to use one of those. To check all supported versions, see the
`Travis file <https://github.com/piccolo-orm/piccolo/blob/master/.travis.yml>`_.

What about other databases?
---------------------------

At the moment the focus is on providing the best Postgres experience possible,
along with some SQLite support. Other databases may be supported in the future.
