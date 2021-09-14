from __future__ import annotations

import typing as t
from dataclasses import dataclass

import pydantic

from piccolo.conf.apps import Finder
from piccolo.utils.pydantic import create_pydantic_model

if t.TYPE_CHECKING:
    from piccolo.table import Table


@dataclass
class FixtureConfig:
    app_name: str
    table_class_names: t.List[str]


def create_pydantic_fixture_model(fixture_configs: t.List[FixtureConfig]):
    """
    Returns a nested Pydantic model for serialising and deserialising fixtures.
    """
    columns: t.Dict[str, t.Any] = {}

    finder = Finder()

    for fixture_config in fixture_configs:

        app_columns: t.Dict[str, t.Any] = {}

        for table_class_name in fixture_config.table_class_names:
            table_class: t.Type[Table] = finder.get_table_with_name(
                app_name=fixture_config.app_name,
                table_class_name=table_class_name,
            )
            app_columns[table_class_name] = (
                t.List[  # type: ignore
                    create_pydantic_model(
                        table_class, include_default_columns=True
                    )
                ],
                ...,
            )

        app_model: t.Any = pydantic.create_model(
            f"{fixture_config.app_name.title()}Model", **app_columns
        )

        columns[fixture_config.app_name] = (app_model, ...)

    model: t.Type[pydantic.BaseModel] = pydantic.create_model(
        "FixtureModel", **columns
    )

    return model
