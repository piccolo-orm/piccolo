.. _Security:

Security
========

SQL Injection protection
------------------------

If you look under the hood, Piccolo uses a custom class called `QueryString`
for composing queries. It keeps query parameters separate from the query
string, so we can pass parameterised queries to the engine. This helps
prevent SQL Injection attacks.
