===================
Supported Databases
===================

Postgres
========
Currently only Postgres is supported.

There's no reason that other DBs couldn't be supported in the future, however the reason it hasn't been prioritised is as follows:

Not currently supported
=======================

SQLite
------
Arguably not as relevant with asyncio because there's no network lag.

MySQL
-----
Since the supported version of Python is 3.7, and asyncio is also very new, we mostly envisage Aragorm being used on greenfield projects.

In the author's opinion, MySQL offers little that Postgres doesn't, for the majority of use cases - making the effort to support it seem somewhat wasted, as opposed to offering as good a Postgres experience as possible.
