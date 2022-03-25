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

create
~~~~~~

Creates a new user. It presents an interactive prompt, asking for the username,
password etc.

.. code-block:: bash

    piccolo user create

If you'd prefer to create a user without the interactive prompt (perhaps in a
script), you can pass all of the arguments in as follows:

.. code-block:: bash

    piccolo user create --username=bob --password=bob123 --email=foo@bar.com  --is_admin=t --is_superuser=t --is_active=t

.. warning::
   If you choose this approach then be careful, as the password will be in the
   shell's history.

change_password
~~~~~~~~~~~~~~~

Change a user's password.

.. code-block:: bash

    piccolo user change_password

change_permissions
~~~~~~~~~~~~~~~~~~

Change a user's permissions. The options are ``--admin``, ``--superuser`` and
``--active``, which change the corresponding attributes on ``BaseUser``.

For example:

.. code-block:: bash

    piccolo user change_permissions some_user --active=true

The :ref:`Piccolo Admin<PiccoloAdmin>` uses these attributes to control who
can login and what they can do.

* **active** and **admin** - must be true for a user to be able to login.
* **superuser** - must be true for a user to be able to change other user's
  passwords.

-------------------------------------------------------------------------------

Within your code
----------------

create_user / create_user_sync
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To create a new user:

.. code-block:: python

    # From within a coroutine:
    await BaseUser.create_user(username="bob", password="abc123", active=True)

    # When not in an event loop:
    BaseUser.create_user_sync(username="bob", password="abc123", active=True)

It saves the user in the database, and returns the created ``BaseUser``
instance.

.. note:: It is preferable to use this rather than instantiating and saving
    ``BaseUser`` directly, as we add additional validation.

login / login_sync
~~~~~~~~~~~~~~~~~~

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

-------------------------------------------------------------------------------

Limits
------

The maximum password length allowed is 128 characters. This should be
sufficiently long for most use cases.

-------------------------------------------------------------------------------

Extending ``BaseUser``
----------------------

If you want to extend ``BaseUser`` with additional fields, we recommend creating
a ``Profile`` table with a ``ForeignKey`` to ``BaseUser``, which can include
any custom fields.

.. code-block:: python

    from piccolo.apps.user.tables import BaseUser
    from piccolo.columns import ForeignKey, Text, Varchar
    from piccolo.table import Table

    class Profile(Table):
        custom_user = ForeignKey(BaseUser)
        phone_number = Varchar()
        bio = Text()

Alternatively, you can copy the entire `user app <https://github.com/piccolo-orm/piccolo/tree/master/piccolo/apps/user>`_ into your
project, and customise it to fit your needs.

----------------------------------------------------------------------------------

Source
------

.. currentmodule:: piccolo.apps.user.tables

.. autoclass:: BaseUser
    :members: create_user, create_user_sync, login, login_sync, update_password, update_password_sync
