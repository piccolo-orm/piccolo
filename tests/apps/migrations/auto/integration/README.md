# Integration tests

The integration tests are for testing the migrations end to end - from auto generating a migration file, to running it.

Migrations are complex - columns can be added, deleted, renamed, and modified (likewise with tables). Migrations can also be run backwards. To properly test all of the possible options, we need a lot of test cases.
