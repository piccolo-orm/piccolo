from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import TYPE_CHECKING

from piccolo.querystring import QueryString, Selectable

if TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.base import Column


@dataclass
class Readable(Selectable):
    """
    This allows a table to specify a 'readable' representation, which can be
    used instead of the primary key in GUIs. See the 'get_readable' Table
    method.
    """

    template: str
    columns: Sequence[Column]
    output_name: str = "readable"

    @property
    def _columns_string(self) -> str:
        return ", ".join(
            i._meta.get_full_name(with_alias=False) for i in self.columns
        )

    def _get_string(self, operator: str) -> QueryString:
        return QueryString(
            f"{operator}('{self.template}', {self._columns_string}) AS "
            f"{self.output_name}"
        )

    @property
    def sqlite_string(self) -> QueryString:
        return self._get_string(operator="PRINTF")

    @property
    def postgres_string(self) -> QueryString:
        return self._get_string(operator="FORMAT")

    @property
    def cockroach_string(self) -> QueryString:
        return self._get_string(operator="FORMAT")

    @property
    def mysql_string(self) -> QueryString:
        """
        MySQL has no FORMAT for string templates, so we manually
        expand placeholders into a CONCAT() expression.
        """
        parts: list[str] = []
        template_parts = self.template.split("%s")
        num_placeholders = len(template_parts) - 1

        for i, part in enumerate(template_parts):
            # Add literal string part
            if part:
                parts.append(f"'{part}'")
            # Add column if within placeholders
            if i < num_placeholders:
                col = self.columns[i]._meta.get_full_name(with_alias=False)
                parts.append(col)

        concat_expr = f"CONCAT({', '.join(parts)})"
        return QueryString(f"{concat_expr} AS {self.output_name}")

    def get_select_string(
        self, engine_type: str, with_alias=True
    ) -> QueryString:
        try:
            return getattr(self, f"{engine_type}_string")
        except AttributeError as e:
            raise ValueError(
                f"Unrecognised engine_type - received {engine_type}"
            ) from e
