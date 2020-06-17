# Piccolo

[![Build Status](https://travis-ci.com/piccolo-orm/piccolo.svg?branch=master)](https://travis-ci.com/piccolo-orm/piccolo)
[![Coverage Status](https://coveralls.io/repos/github/piccolo-orm/piccolo/badge.svg)](https://coveralls.io/github/piccolo-orm/piccolo)
[![Documentation Status](https://readthedocs.org/projects/piccolo-orm/badge/?version=latest)](https://piccolo-orm.readthedocs.io/en/latest/?badge=latest)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/context:python)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/piccolo-orm/piccolo.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/piccolo-orm/piccolo/alerts/)

A fast, user friendly ORM and query builder which supports asyncio. [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/).

Some of it’s stand out features are:

- Support for sync and async.
- A builtin playground, which makes learning a breeze.
- Tab completion support - works great with iPython and VSCode.
- Batteries included - a User model, authentication, migrations, an [admin GUI](https://github.com/piccolo-orm/piccolo_admin), and more.
- Modern Python - fully type annotated.

The syntax is clean and expressive.

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
    (Band.band_members == 0) | (Band.manager.status == 'disabled')
).run()

# Update:
await Band.update({Band.members: 5}).where(
    Band.name == 'Pythonistas'
).run()
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

## Documentation

See [Read the docs](https://piccolo-orm.readthedocs.io/en/latest/piccolo/getting_started/index.html).
