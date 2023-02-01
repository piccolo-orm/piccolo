"""
Dataclasses for storing lazy references between ForeignKey columns and tables.
"""
from __future__ import annotations

import typing as t
from dataclasses import dataclass, field

if t.TYPE_CHECKING:  # pragma: no cover
    from piccolo.columns.column_types import ForeignKey
    from piccolo.table import Table


@dataclass
class SetReadyResponse:
    is_ready: bool
    was_changed: bool


@dataclass
class LazyTableReference:
    """
    Holds a reference to a :class:`Table <piccolo.table.Table>` subclass. Used
    to avoid circular dependencies in the ``references`` argument of
    :class:`ForeignKey <piccolo.columns.column_types.ForeignKey>` columns.
    Pass in either ``app_name`` OR ``module_path``.

    :param table_class_name:
        The name of the ``Table`` subclass. For example, ``'Manager'``.
    :param app_name:
        If specified, the ``Table`` subclass is imported from a Piccolo app
        with the given name.
    :param module_path:
        If specified, the ``Table`` subclass is imported from this path.
        For example, ``'my_app.tables'``.

    """

    table_class_name: str
    app_name: t.Optional[str] = None
    module_path: t.Optional[str] = None

    def __post_init__(self):
        if self.app_name is None and self.module_path is None:
            raise ValueError(
                "You must specify either app_name or module_path."
            )
        if self.app_name and self.module_path:
            raise ValueError(
                "Specify either app_name or module_path - not both."
            )
        # We should only try resolving it once it is ready. We know it's ready
        # because the table metaclass sets this to `True` when the
        # corresponding table has been initialised.
        self.ready = False
        self._resolved: t.Optional[t.Table] = None

    def check_ready(
        self, table_classes: t.List[t.Type[Table]]
    ) -> SetReadyResponse:
        """
        Checks to see if the table being referenced is in the provided list,
        meaning it has successfully loaded.
        """
        if self.ready:
            return SetReadyResponse(is_ready=True, was_changed=False)
        else:
            for table_class in table_classes:
                if self.table_class_name == table_class.__name__:
                    if (
                        self.module_path
                        and self.module_path == table_class.__module__
                    ) or (
                        self.app_name
                        and self.app_name == table_class._meta.app_name
                    ):
                        self.ready = True
                        return SetReadyResponse(
                            is_ready=True, was_changed=True
                        )

        return SetReadyResponse(is_ready=False, was_changed=False)

    def resolve(self) -> t.Type[Table]:
        if self._resolved is not None:
            return self._resolved

        if self.app_name is not None:
            from piccolo.conf.apps import Finder

            finder = Finder()
            table_class = finder.get_table_with_name(
                app_name=self.app_name, table_class_name=self.table_class_name
            )
            self._resolved = table_class
            return table_class

        if self.module_path:
            from piccolo.table import TABLE_REGISTRY

            for table_class in TABLE_REGISTRY:
                if (
                    table_class.__name__ == self.table_class_name
                    and table_class.__module__ == self.module_path
                ):
                    self._resolved = table_class
                    return table_class

            raise ValueError(
                "Can't find a Table subclass called "
                f"{self.table_class_name} in {self.module_path}"
            )

        raise ValueError("You must specify either app_name or module_path.")

    def __str__(self):
        if self.app_name:
            return f"App {self.app_name}.{self.table_class_name}"
        elif self.module_path:
            return f"Module {self.module_path}.{self.table_class_name}"
        else:
            return "Unknown"


@dataclass
class LazyColumnReferenceStore:
    # Foreign key columns which use LazyTableReference.
    foreign_key_columns: t.List[ForeignKey] = field(default_factory=list)

    def check_ready(self, table_class: t.Type[Table]):
        """
        The ``Table`` metaclass calls this once a ``Table`` has been imported.
        It tells each ``LazyTableReference`` which references that table that
        it's ready.
        """
        for foreign_key_column in self.foreign_key_columns:
            reference = t.cast(
                LazyTableReference,
                foreign_key_column._foreign_key_meta.references,
            )
            if reference.check_ready(table_classes=[table_class]).was_changed:
                foreign_key_column._on_ready()

    def for_table(self, table: t.Type[Table]) -> t.List[ForeignKey]:
        return [
            i
            for i in self.foreign_key_columns
            if isinstance(i._foreign_key_meta.references, LazyTableReference)
            and i._foreign_key_meta.references.resolve() is table
        ]

    def for_tablename(self, tablename: str) -> t.List[ForeignKey]:
        return [
            i
            for i in self.foreign_key_columns
            if isinstance(i._foreign_key_meta.references, LazyTableReference)
            and i._foreign_key_meta.references.resolve()._meta.tablename
            == tablename
        ]


LAZY_COLUMN_REFERENCES: LazyColumnReferenceStore = LazyColumnReferenceStore()
