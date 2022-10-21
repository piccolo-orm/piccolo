"Logic for gathering and managing the configuration settings"

import configparser
from dataclasses import dataclass, fields
from itertools import chain
from pathlib import Path
from typing import ClassVar, Collection, Mapping, Optional, Type, TypeVar

import tomli

from .common import add_slots, both

RegexStr = str
"A regex string in Python's verbose syntax"
DEFAULT_MODULE_EXCLUDE_RE = r"(^|\.)__main__(\.|$)"
_T = TypeVar("_T")


@add_slots
@dataclass(frozen=True)
class PartialConfig:
    "Configuration options where not all options may be defined."
    strict_imports: Optional[bool]
    require_subclass: Optional[bool]
    require_superclass: Optional[bool]
    include_modules: Optional[RegexStr]
    exclude_modules: Optional[RegexStr]
    include_classes: Optional[RegexStr]
    exclude_classes: Optional[RegexStr]

    EMPTY: ClassVar["PartialConfig"]

    @classmethod
    def load(cls, p: Path) -> "PartialConfig":
        "May raise various exceptions on parse problems. File must exist."
        if p.suffix == ".toml":
            return cls._load_toml(p)
        elif p.suffix in (".ini", ".cfg"):
            return cls._load_ini(p)
        else:
            raise ValueError(
                "Settings file with invalid extension. "
                "Expected .toml, .ini, or .cfg"
            )

    @classmethod
    def _load_toml(cls, p: Path) -> "PartialConfig":
        with p.open("rb") as rfile:
            return cls._load_confmap(
                tomli.load(rfile).get("tool", {}).get("slotscheck", {})
            )

    @classmethod
    def _load_ini(cls, p: Path) -> "PartialConfig":
        cfg = configparser.ConfigParser()
        cfg.read(p, encoding="utf-8")
        return cls._load_confmap(
            {
                k: cfg.BOOLEAN_STATES.get(v, v)
                for k, v in cfg.items("slotscheck")
            }
            if cfg.has_section("slotscheck")
            else {}
        )

    @classmethod
    def _load_confmap(cls, m: Mapping[str, object]) -> "PartialConfig":
        if not m.keys() <= _ALLOWED_KEYS.keys():
            raise InvalidKeys(m.keys() - _ALLOWED_KEYS)

        return PartialConfig(
            **{
                key.replace("-", "_"): _extract_value(m, key, expect_type)
                for key, expect_type in _ALLOWED_KEYS.items()
            },
        )


PartialConfig.EMPTY = PartialConfig(None, None, None, None, None, None, None)


@dataclass(frozen=True)
class Config(PartialConfig):
    "A full set of options"
    __slots__ = ()
    strict_imports: bool
    require_subclass: bool
    require_superclass: bool
    exclude_modules: RegexStr

    DEFAULT: ClassVar["Config"]

    def apply(self, other: PartialConfig) -> "Config":
        return Config(
            **{
                f.name: _none_or(getattr(other, f.name), getattr(self, f.name))
                for f in fields(PartialConfig)
            }
        )


Config.DEFAULT = Config(
    strict_imports=False,
    require_subclass=False,
    require_superclass=True,
    include_modules=None,
    exclude_modules=DEFAULT_MODULE_EXCLUDE_RE,
    include_classes=None,
    exclude_classes=None,
)


def collect(
    from_cli: PartialConfig, cwd: Path, config: Optional[Path]
) -> Config:
    "Gather and combine configuration options from the available sources"
    confpath = config or find_config_file(cwd)
    conf = PartialConfig.load(confpath) if confpath else PartialConfig.EMPTY
    return Config.DEFAULT.apply(conf).apply(from_cli)


_CONFIG_FILENAMES = ("pyproject.toml", "setup.cfg")


def find_config_file(path: Path) -> Optional[Path]:
    "Find a configuration file in the given directory or its parents"
    candidates = (
        directory / name
        for directory in chain((path,), path.parents)
        for name in _CONFIG_FILENAMES
    )
    return next(
        filter(
            both(
                Path.is_file,  # type: ignore[arg-type]
                _has_slotscheck_section,  # type: ignore[arg-type]
            ),
            candidates,
        ),
        None,
    )


def _has_slotscheck_section(p: Path) -> bool:
    with p.open("rb") as rfile:
        if p.suffix == ".toml":
            return "slotscheck" in tomli.load(rfile).get("tool", {})
        else:
            assert p.suffix == ".cfg"
            cfg = configparser.ConfigParser()
            cfg.read(p, encoding="utf-8")
            return cfg.has_section("slotscheck")


class InvalidKeys(Exception):
    def __init__(self, keys: Collection[str]) -> None:
        self.keys = keys

    def __str__(self) -> str:
        return (
            "Invalid configuration key(s): "
            + ", ".join(map("'{}'".format, sorted(self.keys)))
            + "."
        )


class InvalidValueType(Exception):
    def __init__(self, key: str) -> None:
        self.key = key

    def __str__(self) -> str:
        return f"Invalid value type for '{self.key}'."


def _none_or(a: Optional[_T], b: _T) -> _T:
    return b if a is None else a


def _extract_value(
    c: Mapping[str, object], key: str, expect_type: Type[_T]
) -> Optional[_T]:
    try:
        raw_value = c[key]
    except KeyError:
        return None
    else:
        if isinstance(raw_value, expect_type):
            return raw_value
        else:
            raise InvalidValueType(key)


_ALLOWED_KEYS = {
    "strict-imports": bool,
    "require-subclass": bool,
    "require-superclass": bool,
    "include-modules": str,
    "exclude-modules": str,
    "include-classes": str,
    "exclude-classes": str,
}
