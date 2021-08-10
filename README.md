# Piccolo

![Tests](https://github.com/piccolo-orm/piccolo/actions/workflows/tests.yaml/badge.svg)
![Release](https://github.com/piccolo-orm/piccolo/actions/workflows/release.yaml/badge.svg)
[![Documentation Status](https://readthedocs.org/projects/piccolo-orm/badge/?version=latest)](https://piccolo-orm.readthedocs.io/en/latest/?badge=latest)
[![PyPI](https://img.shields.io/pypi/v/piccolo?color=%2334D058&label=pypi)](https://pypi.org/project/piccolo/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/alerts/)
[![codecov](https://codecov.io/gh/piccolo-orm/piccolo/branch/master/graph/badge.svg?token=V19CWH7MXX)](https://codecov.io/gh/piccolo-orm/piccolo)

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

Installing with PostgreSQL driver:

```
pip install 'piccolo[postgres]'
```

Installing with SQLite driver:

```
pip install 'piccolo[sqlite]'
```

## Building a web app?

Let Piccolo scaffold you an ASGI web app, using Piccolo as the ORM:

```
piccolo asgi new
```

[Starlette](https://www.starlette.io/), [FastAPI](https://fastapi.tiangolo.com/), and [BlackSheep](https://www.neoteroi.dev/blacksheep/) are currently supported.

## Are you a Django user?

We have a handy page which shows the equivalent of [common Django queries in Piccolo](https://piccolo-orm.readthedocs.io/en/latest/piccolo/query_types/django_comparison.html).

## Documentation

See [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/piccolo/getting_started/index.html).
