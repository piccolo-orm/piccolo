.. _BaseUser:

BaseUser
========

Inherit from ``BaseUser`` to create your own User table.

.. code-block:: python

    from piccolo.extensions.user import BaseUser


    class User(BaseUser, tablename="custom_user"):
        pass

.. hint:: A table name of `user` isn't allowed since it clashes with a keyword in Postgres - so override the ``tablename``, if you choose to name your class ``User``.

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

update_password / update_password_sync
--------------------------------------

To change a user's password:

.. code-block:: python

    # From within a coroutine:
    await User.update_password(username="bob", password="abc123")

    # When not in an event loop:
    User.update_password_sync(username="bob", password="abc123")

.. warning:: Don't use bulk updates for passwords - use ``update_password`` /
   ``update_password_sync``, and they'll correctly hash the password.
