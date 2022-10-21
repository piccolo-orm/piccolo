from __future__ import annotations

import asyncio
import decimal
import inspect
import json
import sys
import traceback
import typing as t
from dataclasses import dataclass, field

try:
    from typing import get_args, get_origin  # type: ignore
except ImportError:
    # For Python 3.7 support
    from typing_extensions import get_args, get_origin

from docstring_parser import Docstring, DocstringParam, parse  # type: ignore

from .format import Color, format_text, get_underline

__VERSION__ = "0.3.7"


# If an annotation is one of these values, we will convert the string value
# to it.
CONVERTABLE_TYPES = (int, float, decimal.Decimal)


@dataclass
class Arguments:
    args: t.List[str] = field(default_factory=list)
    kwargs: t.Dict[str, t.Any] = field(default_factory=dict)


@dataclass
class Command:
    """
    Represents a CLI command.

    :param command:
        The Pyton function or coroutine which gets called.
    :param group_name:
        Commands can belong to a group. In this situation, the group name must
        appear before the command name when called from the command line. For
        example `python my_file.py group_name command_name`.
    :param command_name:
        By default the command name is the same as the callable, but it can
        be overriden here.
    :param aliases:
        You can provide aliases, which can be abbreviations or common
        mispellings. For example, for a `command_name` of ``run``, we could
        have aliases like ``['start', 'rn']``.

    """
    command: t.Callable
    group_name: t.Optional[str] = None
    command_name: t.Optional[str] = None
    aliases: t.List[str] = field(default_factory=list)

    def __post_init__(self):
        self.command_docstring: Docstring = parse(self.command.__doc__)
        self.annotations = t.get_type_hints(self.command)
        self.signature = inspect.signature(self.command)
        self.solo = False
        if not self.command_name:
            self.command_name = self.command.__name__

    @property
    def full_name(self):
        return (
            f"{self.group_name} {self.command_name}"
            if self.group_name
            else self.command_name
        )

    @property
    def description(self) -> str:
        docstring: Docstring = parse(self.command.__doc__ or "")
        return " ".join(
            [
                docstring.short_description or "",
                docstring.long_description or "",
            ]
        )

    def _get_docstring_param(self, arg_name) -> t.Optional[DocstringParam]:
        for param in self.command_docstring.params:
            if param.arg_name == arg_name:
                return param
        return None

    def _get_arg_description(self, arg_name: str) -> str:
        docstring_param = self._get_docstring_param(arg_name)
        if docstring_param:
            return docstring_param.description or ""
        else:
            return ""

    def _get_arg_default(self, arg_name: str):
        parameter = self.signature.parameters.get(arg_name)
        if parameter:
            default = parameter.default
            if default is not inspect._empty:  # type: ignore
                return default
        return None

    @property
    def arguments_description(self) -> str:
        """
        :returns: A string containing a description for each argument.
        """
        output = []

        for arg_name, _ in self.annotations.items():
            arg_description = self._get_arg_description(arg_name=arg_name)

            arg_default = self._get_arg_default(arg_name=arg_name)
            arg_default_json = json.dumps(arg_default)

            default_str = (
                f"[default={arg_default_json}]"
                if arg_default is not None
                else ""
            )

            output.append(
                format_text(arg_name, color=Color.cyan) + f" {default_str}"
            )
            if arg_description:
                output.append(arg_description)
            output.append("")

        return "\n".join(output)

    @property
    def usage(self) -> str:
        """
        Example:

        some_command required_arg [--optional_arg=value] [--some_flag]
        """
        if self.solo:
            output = []
        else:
            command_name = self.command_name or ""
            output = [format_text(command_name, color=Color.green)]

        for arg_name, parameter in self.signature.parameters.items():
            if parameter.default is inspect._empty:  # type: ignore
                output.append(format_text(arg_name, color=Color.cyan))
            else:
                if parameter.default is False:
                    output.append(
                        format_text(f"[--{arg_name}]", color=Color.cyan)
                    )
                else:
                    output.append(
                        format_text(f"[--{arg_name}=X]", color=Color.cyan)
                    )

        return " ".join(output)

    def print_help(self):
        print("")
        print(self.command_name)
        print(get_underline(len(self.command_name)))
        print(self.description)

        print("")
        print("Usage")
        print(get_underline(5, character="-"))
        print(self.usage)
        print("")

        print("Args")
        print(get_underline(4, character="-"))
        if self.arguments_description:
            print(self.arguments_description)
        else:
            print("No args\n")

        if self.aliases:
            print("Aliases")
            print(get_underline(7, character="-"))
            alias_string = ", ".join(self.aliases)
            print(format_text(alias_string, color=Color.green))
        print("")

    def call_with(self, arg_class: Arguments):
        """
        Call the command function with the given arguments.

        The arguments are all strings at this point, as they're come from the
        command line.

        """
        if arg_class.kwargs.get("help"):
            self.print_help()
            return

        annotations = t.get_type_hints(self.command)

        kwargs = arg_class.kwargs.copy()
        for index, value in enumerate(arg_class.args):
            key = inspect.getfullargspec(self.command).args[index]
            kwargs[key] = value

        cleaned_kwargs = {}

        for key, value in kwargs.items():
            annotation = annotations.get(key)
            # This only works with basic types like str at the moment.

            if annotation in CONVERTABLE_TYPES:
                value = annotation(value)
            elif get_origin(annotation) is t.Union:  # type: ignore
                # t.Union is used to detect t.Optional
                inner_annotations = get_args(annotation)
                filtered = [i for i in inner_annotations if i is not None]
                if len(filtered) == 1:
                    annotation = filtered[0]
                    if annotation in CONVERTABLE_TYPES:
                        value = annotation(value)

            cleaned_kwargs[key] = value

        if inspect.iscoroutinefunction(self.command):
            asyncio.run(self.command(**cleaned_kwargs))
        else:
            self.command(**cleaned_kwargs)


@dataclass
class CLI:
    """
    The root class for building the CLI.

    Example usage:

    .. code-block:: python

        cli = CLI()
        cli.register(some_function)

    :param description:
        Customise the title of your CLI tool.

    """

    description: str = "Targ CLI"
    commands: t.List[Command] = field(default_factory=list, init=False)

    def command_exists(self, group_name: str, command_name: str) -> bool:
        """
        This isn't used by Targ itself, but is useful for third party code
        which wants to inspect the CLI, to find if a command with the given
        name exists.
        """
        for command in self.commands:
            if (
                command.group_name == group_name
                and command.command_name == command_name
            ):
                return True
        return False

    def _validate_name(self, name: str) -> bool:
        """
        Any custom names provided by user should not contain spaces (i.e.
        command names and group names).
        """
        if " " in name:
            return False
        return True

    def register(
        self,
        command: t.Callable,
        group_name: t.Optional[str] = None,
        command_name: t.Optional[str] = None,
        aliases: t.List[str] = [],
    ):
        """
        Register a function or coroutine as a CLI command.

        :param command:
            The function or coroutine to register as a CLI command.
        :param group_name:
            If specified, the CLI command will belong to a group. When calling
            a command which belongs to a group, it must be prefixed with the
            ``group_name``. For example
            ``python my_file.py group_name command_name``.
        :param command_name:
            By default, the name of the CLI command will be the same as the
            function or coroutine which is being called. You can override this
            here.
        :param aliases:
            The command can also be accessed using these aliases.

        """
        if group_name and not self._validate_name(group_name):
            raise ValueError("The group name should not contain spaces.")

        if command_name and not self._validate_name(command_name):
            raise ValueError("The command name should not contain spaces.")

        self.commands.append(
            Command(
                command=command,
                group_name=group_name,
                command_name=command_name,
                aliases=aliases,
            )
        )

    def get_help_text(self) -> str:
        lines = [
            "",
            self.description,
            get_underline(len(self.description)),
            (
                "Enter the name of a command followed by --help to learn "
                "more."
            ),
            "",
            "",
            "Commands",
            "--------",
        ]

        for command in self.commands:
            lines.append(format_text(command.full_name, color=Color.green))
            lines.append(command.description)
            lines.append("")

        return "\n".join(lines)

    def _get_cleaned_args(self) -> t.List[str]:
        """
        Remove any redundant arguments.
        """
        return sys.argv[1:]

    def _get_command(
        self, command_name: str, group_name: t.Optional[str] = None
    ) -> t.Optional[Command]:
        for command in self.commands:
            if (
                command.command_name == command_name
                or command_name in command.aliases
            ):
                if group_name and command.group_name != group_name:
                    continue
                return command
        return None

    def _clean_cli_argument(self, value: str) -> t.Any:
        if value in ["True", "true", "t"]:
            return True
        elif value in ["False", "false", "f"]:
            return False
        return value

    def _get_arg_class(self, args: t.List[str]) -> Arguments:
        arguments = Arguments()
        for arg_str in args:
            if arg_str.startswith("--"):
                components = arg_str[2:].split("=", 1)
                if len(components) == 2:
                    # For value arguments, like --user=bob
                    name = components[0]
                    value = self._clean_cli_argument(components[1])
                else:
                    # For flags, like --verbose.
                    name = components[0]
                    value = True

                arguments.kwargs[name] = value
            else:
                value = self._clean_cli_argument(arg_str)
                arguments.args.append(value)
        return arguments

    @property
    def _can_run_in_solo_mode(self) -> bool:
        return len(self.commands) == 1

    def run(self, solo: bool = False):
        """
        Run the CLI.

        :param solo:
            By default, a command name must be given when running the CLI, for
            example ``python my_file.py command_name``. In some situations, you
            may only have a single command registered with the CLI, so passing
            in the command name is redundant. If ``solo=True``, you can omit
            the command name i.e. ``python my_file.py``, and Targ will
            automatically call the single registered command.

        """
        cleaned_args = self._get_cleaned_args()
        command: t.Optional[Command] = None

        # Work out if to enable tracebacks
        try:
            index = cleaned_args.index("--trace")
        except ValueError:
            trace = False
        else:
            cleaned_args.pop(index)
            trace = True

        if solo:
            if not self._can_run_in_solo_mode:
                print(
                    "Error - solo mode is only allowed if a single command is "
                    "registered with the CLI."
                )
                return
            command_name = ""
            command = self.commands[0]
            command.solo = True
        else:
            if len(cleaned_args) == 0:
                print(self.get_help_text())
                return

            command_name = cleaned_args[0]
            command = self._get_command(command_name=command_name)
            if command:
                cleaned_args = cleaned_args[1:]

        if not command:
            # See if it belongs to a group:
            if len(cleaned_args) >= 2:
                group_name = cleaned_args[0]
                command_name = cleaned_args[1]
                command = self._get_command(
                    command_name=command_name, group_name=group_name
                )
                if command:
                    cleaned_args = cleaned_args[2:]

        if command:
            try:
                arg_class = self._get_arg_class(cleaned_args)
                command.call_with(arg_class)
            except Exception as exception:
                print(format_text("The command failed.", color=Color.red))
                print(exception)

                if trace:
                    print(traceback.format_exc())
                else:
                    print("For a full stack trace, use --trace")

                command.print_help()
                sys.exit(1)
        else:
            print(f"Unrecognised command - {command_name}")
            print(self.get_help_text())
