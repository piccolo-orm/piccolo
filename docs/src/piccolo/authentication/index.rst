.. _Authentication:

Authentication
==============

Piccolo ships with authentication support out of the box.

-------------------------------------------------------------------------------

Registering the app
-------------------

Make sure ``'piccolo.apps.user.piccolo_app'`` is in your ``AppRegistry`` (see
:ref:`PiccoloProjects`).

-------------------------------------------------------------------------------

Tables
------

.. toctree::
    :maxdepth: 1

    ./baseuser

-------------------------------------------------------------------------------

Web app integration
-------------------

Our sister project, `Piccolo API <https://piccolo-api.readthedocs.io/en/latest/index.html>`_,
contains powerful endpoints and middleware for integrating
`session auth <https://piccolo-api.readthedocs.io/en/latest/session_auth/index.html>`_
and `token auth <https://piccolo-api.readthedocs.io/en/latest/token_auth/index.html>`_
into your ASGI web application, using ``BaseUser``.
