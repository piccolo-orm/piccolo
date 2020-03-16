from dataclasses import dataclass
import typing as t


@dataclass
class AppConfig:
    apps = t.List[str]

    def __post_init__(self):
        pass
