from __future__ import annotations

import typing as t
from dataclasses import dataclass

from piccolo.columns.base import Selectable


@dataclass
class Readable(Selectable):
    """
    This allows a table to specify a 'readable' representation, which can be
    used instead of the primary key in GUIs. See the 'get_readable' Table
    method.
    """

    template: str
    columns: t.Sequence[Selectable]
    output_name: str = "readable"

    def _get_columns_string(self, engine_type: str) -> str:
        return ", ".join(
            i.get_select_string(engine_type=engine_type, with_alias=False)
            for i in self.columns
        )

    def _get_string(self, operator: str, engine_type: str) -> str:
        columns_string = self._get_columns_string(engine_type=engine_type)
        return (
            f"{operator}('{self.template}', {columns_string}) AS "
            f"{self.output_name}"
        )

    @property
    def sqlite_string(self) -> str:
        return self._get_string(operator="PRINTF", engine_type="sqlite")

    @property
    def postgres_string(self) -> str:
        return self._get_string(operator="FORMAT", engine_type="postgres")

    @property
    def cockroach_string(self) -> str:
        return self._get_string(operator="FORMAT", engine_type="cockroach")

    def get_select_string(self, engine_type: str, with_alias=True) -> str:
        try:
            return getattr(self, f"{engine_type}_string")
        except AttributeError as e:
            raise ValueError(
                f"Unrecognised engine_type - received {engine_type}"
            ) from e
