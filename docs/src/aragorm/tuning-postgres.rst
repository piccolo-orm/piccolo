===============
Tuning Postgres
===============

One of the aims of Aragorm is to get more queries into the database.

So while one request is waiting on a database response, another request can fire off another database request.

You might wonder how Postgres handles this increased load, and how to tune it to process concurrent requests as quickly as possible.

 - https://www.postgresql.org/docs/current/static/mvcc.html
