import os
import sys

from targ import CLI

from piccolo.conf.apps import AppRegistry
from piccolo.apps.app.piccolo_app import APP_CONFIG as app_config
from piccolo.apps.asgi.piccolo_app import APP_CONFIG as asgi_config
from piccolo.apps.meta.piccolo_app import APP_CONFIG as meta_config
from piccolo.apps.migrations.piccolo_app import APP_CONFIG as migrations_config
from piccolo.apps.playground.piccolo_app import APP_CONFIG as playground_config
from piccolo.apps.project.piccolo_app import APP_CONFIG as project_config
from piccolo.apps.user.piccolo_app import APP_CONFIG as user_config


def main():
    # In case it's run from an entrypoint:
    sys.path.insert(0, os.getcwd())

    cli = CLI(description="Piccolo CLI")

    ###########################################################################
    # Register the base apps.

    for _app_config in [
        app_config,
        asgi_config,
        meta_config,
        migrations_config,
        playground_config,
        project_config,
        user_config,
    ]:
        for command in _app_config.commands:
            cli.register(command, group_name=_app_config.app_name)

    ###########################################################################
    # Get user defined apps.

    try:
        import piccolo_conf
    except ImportError:
        print("Can't import piccolo_conf - some commands may be missing.")
    else:
        try:
            APP_REGISTRY: AppRegistry = getattr(piccolo_conf, "APP_REGISTRY")
        except Exception:
            print("Unable to find APP_REGISTRY in piccolo_conf.")
        else:
            for app_name, _app_config in APP_REGISTRY.app_configs.items():
                for command in _app_config.commands:
                    if cli.command_exists(
                        group_name=app_name, command_name=command.__name__
                    ):
                        # Skipping - already registered.
                        continue
                    cli.register(command, group_name=app_name)

    ###########################################################################

    cli.run()


if __name__ == "__main__":
    main()
