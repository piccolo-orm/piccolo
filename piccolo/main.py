import importlib
import os
import sys

import click

from piccolo.commands.playground import playground
from piccolo.commands.migration.new import new
from piccolo.commands.migration.backwards import backwards
from piccolo.commands.migration.forwards import forwards
from piccolo.commands.migration.check import check


@click.group()
def cli():
    pass


@cli.group("migration")
def migration():
    pass


migration.add_command(check)
migration.add_command(new)
migration.add_command(forwards)
migration.add_command(backwards)

cli.add_command(playground)


def main():
    # In case it's run from an entrypoint:
    sys.path.insert(0, os.getcwd())

    try:
        import piccolo_conf
    except ImportError:
        print("Can't import piccolo_conf - some commands may be missing.")
    else:
        COMMANDS = getattr(piccolo_conf, "COMMANDS", [])

        for command in COMMANDS:
            command_name = command.split(".")[-1]
            command_module = importlib.import_module(command)
            command_func = getattr(command_module, "command")
            cli.add_command(click.command(name=command_name)(command_func))

    cli()


if __name__ == "__main__":
    main()
