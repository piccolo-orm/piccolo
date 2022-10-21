# Copyright 2013 Donald Stufft
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import argparse
from typing import Any, List, Tuple

import importlib_metadata
from packaging import requirements

import twine

args = argparse.Namespace()


def list_dependencies_and_versions() -> List[Tuple[str, str]]:
    requires = importlib_metadata.requires("twine")  # type: ignore[no-untyped-call] # python/importlib_metadata#288  # noqa: E501
    deps = [requirements.Requirement(r).name for r in requires]
    return [(dep, importlib_metadata.version(dep)) for dep in deps]  # type: ignore[no-untyped-call] # python/importlib_metadata#288  # noqa: E501


def dep_versions() -> str:
    return ", ".join(
        "{}: {}".format(*dependency) for dependency in list_dependencies_and_versions()
    )


def dispatch(argv: List[str]) -> Any:
    registered_commands = importlib_metadata.entry_points(
        group="twine.registered_commands"
    )
    parser = argparse.ArgumentParser(prog="twine")
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s version {} ({})".format(twine.__version__, dep_versions()),
    )
    parser.add_argument(
        "--no-color",
        default=False,
        required=False,
        action="store_true",
        help="disable colored output",
    )
    parser.add_argument(
        "command",
        choices=registered_commands.names,
    )
    parser.add_argument(
        "args",
        help=argparse.SUPPRESS,
        nargs=argparse.REMAINDER,
    )

    parser.parse_args(argv, namespace=args)

    main = registered_commands[args.command].load()

    return main(args.args)
