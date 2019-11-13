from copy import copy
import importlib
import os
import sys
from types import ModuleType
import typing as t


ModuleDict = t.Dict[str, ModuleType]


def get_migration_modules(
    folder_path: str, recursive=False, migration_modules: ModuleDict = {}
) -> ModuleDict:
    """
    Import the migration modules and store them in a dictionary.
    """
    print(folder_path)
    print(migration_modules)

    migration_modules = copy(migration_modules)

    sys.path.insert(0, folder_path)

    folder_contents = os.listdir(folder_path)
    excluded = ("__init__.py", "__pycache__", "config.py")
    migration_names = [
        i.split(".py")[0]
        for i in folder_contents
        if ((i not in excluded) and (not i.startswith(".")))
    ]
    modules = [importlib.import_module(name) for name in migration_names]
    for m in modules:
        _id = getattr(m, "ID", None)
        if _id:
            migration_modules[_id] = m

    if ("config.py" in folder_contents) and recursive:
        if "config" in sys.modules:
            del sys.modules["config"]
        config_module = importlib.import_module("config")
        dependencies: t.Optional[t.Sequence[str]] = getattr(
            config_module, "DEPENDENCIES", None
        )
        if dependencies:
            for dependency_name in dependencies:
                # if dependency_name in sys.modules:
                #     del sys.modules[dependency_name]
                try:
                    config_module = importlib.import_module(dependency_name)
                except ModuleNotFoundError as e:
                    print(f"Can't import {dependency_name}")
                    import pdb

                    pdb.set_trace()
                    raise (e)
                else:
                    migration_modules = get_migration_modules(
                        folder_path=os.path.dirname(config_module.__file__),
                        recursive=True,
                        migration_modules=migration_modules,
                    )

    return migration_modules


def get_migration_ids(module_dict: ModuleDict) -> t.List[str]:
    return list(module_dict.keys())
