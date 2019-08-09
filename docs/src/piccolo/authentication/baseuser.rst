.. _BaseUser:

BaseUser
========

Inherit from ``BaseUser`` to create your own User table.

.. code-block:: python

    from piccolo.extensions.user import BaseUser


    class User(BaseUser):

        class Meta():
            tablename = 'custom_user'

.. hint:: A table name of `user` isn't allowed since it clashes with a keyword in Postgres - so override the ``tablename`` in ``Meta``, if you choose to name your class ``User``.

login
-----

To login a user, do the following:

.. code-block:: python

    # From within a coroutine:
    await User.login(username="bob", password="abc123")
    >>> 1

    # When not in an event loop:
    User.login_sync(username="bob", password="abc123")
    >>> 1

If the login is successful, the user's id is returned, otherwise ``None`` is
returned.
