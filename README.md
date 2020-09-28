# Piccolo

[![Build Status](https://travis-ci.com/piccolo-orm/piccolo.svg?branch=master)](https://travis-ci.com/piccolo-orm/piccolo)
[![Coverage Status](https://coveralls.io/repos/github/piccolo-orm/piccolo/badge.svg)](https://coveralls.io/github/piccolo-orm/piccolo)
[![Documentation Status](https://readthedocs.org/projects/piccolo-orm/badge/?version=latest)](https://piccolo-orm.readthedocs.io/en/latest/?badge=latest)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/alerts/)

A fast, user friendly ORM and query builder which supports asyncio. [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/).

## Features

Some of it’s stand out features are:

- Support for sync and async.
- A builtin playground, which makes learning a breeze.
- Tab completion support - works great with iPython and VSCode.
- Batteries included - a User model, authentication, migrations, an [admin GUI](https://github.com/piccolo-orm/piccolo_admin), and more.
- Modern Python - fully type annotated.

## Syntax

The syntax is clean and expressive.

You can use it as a query builder:

```python
# Select:
await Band.select(
    Band.name
).where(
    Band.popularity > 100
).run()

# Join:
await Band.select(
    Band.name,
    Band.manager.name
).run()

# Delete:
await Band.delete().where(
    Band.popularity < 1000
).run()

# Update:
await Band.update({Band.popularity: 10000}).where(
    Band.name == 'Pythonistas'
).run()
```

Or like a typical ORM:

```python
# To create a new object:
b = Band(name='C-Sharps', popularity=100)
await b.save().run()

# To fetch an object from the database, and update it:
b = await Band.objects().where(Band.name == 'Pythonistas').first().run()
b.popularity = 10000
await b.save().run()

# To delete:
await b.remove().run()
```

## Installation

```
pip install piccolo
```

## Building a web app?

Let Piccolo scaffold you an ASGI web app, using Piccolo as the ORM:

```
piccolo asgi new
```

[Starlette](https://www.starlette.io/) and [FastAPI](https://fastapi.tiangolo.com/) are currently supported.

## Are you a Django user?

We have a handy page which shows the equivalent of [common Django queries in Piccolo](https://piccolo-orm.readthedocs.io/en/latest/piccolo/query_types/django_comparison.html).

## Documentation

See [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/piccolo/getting_started/index.html).
