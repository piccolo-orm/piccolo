.. _BaseUser:

BaseUser
========

``BaseUser`` is a ``Table`` you can use to store and authenticate your users.

-------------------------------------------------------------------------------

Creating the Table
------------------

Run the migrations:

.. code-block:: bash

    piccolo migrations forwards user

-------------------------------------------------------------------------------

Commands
--------

The app comes with some useful commands.

user create
~~~~~~~~~~~

Create a new user.

.. code-block:: bash

    piccolo user create

user change_password
~~~~~~~~~~~~~~~~~~~~

Change a user's password.

.. code-block:: bash

    piccolo user change_password

user change_permissions
~~~~~~~~~~~~~~~~~~~~~~~

Change a user's permissions. The options are ``--admin``, ``--superuser`` and
``--active``, which change the corresponding attributes on ``BaseUser``.

For example:

.. code-block:: bash

    piccolo user change_permissions some_user --active=true

The Piccolo Admin (see :ref:`Ecosystem`) uses these attributes to control who
can login and what they can do.

 * **active** and **admin** - must be true for a user to be able to login.
 * **superuser** - must be true for a user to be able to change other user's
   passwords.

-------------------------------------------------------------------------------

Within your code
----------------

login
~~~~~

To check a user's credentials, do the following:

.. code-block:: python

    from piccolo.apps.user.tables import BaseUser

    # From within a coroutine:
    >>> await BaseUser.login(username="bob", password="abc123")
    1

    # When not in an event loop:
    >>> BaseUser.login_sync(username="bob", password="abc123")
    1

If the login is successful, the user's id is returned, otherwise ``None`` is
returned.

update_password / update_password_sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To change a user's password:

.. code-block:: python

    # From within a coroutine:
    await BaseUser.update_password(username="bob", password="abc123")

    # When not in an event loop:
    BaseUser.update_password_sync(username="bob", password="abc123")

.. warning:: Don't use bulk updates for passwords - use ``update_password`` /
   ``update_password_sync``, and they'll correctly hash the password.
