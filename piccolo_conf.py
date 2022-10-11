"""
This piccolo_conf file is just here so migrations can be made for Piccolo's own
internal apps.

For example:

python -m piccolo.main migration new user --auto

"""

from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

DB = PostgresEngine(config={})


# A list of paths to piccolo apps
# e.g. ['blog.piccolo_app']
APP_REGISTRY = AppRegistry(apps=["piccolo.apps.user.piccolo_app"])
