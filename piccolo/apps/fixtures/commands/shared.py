from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import pydantic

from piccolo.conf.apps import Finder
from piccolo.utils.pydantic import create_pydantic_model

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.table import Table


@dataclass
class FixtureConfig:
    app_name: str
    table_class_names: list[str]


def create_pydantic_fixture_model(fixture_configs: list[FixtureConfig]):
    """
    Returns a nested Pydantic model for serialising and deserialising fixtures.
    """
    columns: dict[str, Any] = {}

    finder = Finder()

    for fixture_config in fixture_configs:

        app_columns: dict[str, Any] = {}

        for table_class_name in fixture_config.table_class_names:
            table_class: type[Table] = finder.get_table_with_name(
                app_name=fixture_config.app_name,
                table_class_name=table_class_name,
            )
            app_columns[table_class_name] = (
                list[  # type: ignore
                    create_pydantic_model(
                        table_class, include_default_columns=True
                    )
                ],
                ...,
            )

        app_model: Any = pydantic.create_model(
            f"{fixture_config.app_name.title()}Model", **app_columns
        )

        columns[fixture_config.app_name] = (app_model, ...)

    return pydantic.create_model("FixtureModel", **columns)
