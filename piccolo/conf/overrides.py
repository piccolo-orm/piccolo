import logging
import os
import typing as t

try:
    import tomllib  # type: ignore
except ImportError:
    import tomli as tomllib


logger = logging.getLogger(__name__)


class OverrideLoader:
    """
    The user can optionally add a ``piccolo_overrides.toml`` file at the root
    of their project (wherever the Python interpreter will be started).

    This can be used to modify some of the internal workings of Piccolo.
    Examples are the ``tablename`` and ``schema`` of the ``Migration`` table.

    The reason we don't have these values in ``piccolo_conf.py`` is we want the
    values to be static. Also, they could be required at any point by Piccolo,
    before the app has fully loaded all of the Python code, so having a static
    file helps prevent circular imports.

    """

    _toml_contents: t.Optional[t.Dict[str, t.Any]]

    def __init__(
        self,
        toml_file_name: str = "piccolo_overrides.toml",
        folder_path: t.Optional[str] = None,
    ):
        self.toml_file_name = toml_file_name
        self.folder_path = folder_path or os.getcwd()
        self._toml_contents = None

    def get_toml_contents(self) -> t.Dict[str, t.Any]:
        """
        Returns the contents of the TOML file.
        """
        if self._toml_contents is None:
            toml_file_path = os.path.join(
                self.folder_path,
                self.toml_file_name,
            )

            if os.path.exists(toml_file_path):
                with open(toml_file_path, "rb") as f:
                    self._toml_contents = tomllib.load(f)
            else:
                raise FileNotFoundError("The TOML file wasn't found.")

        return self._toml_contents

    def get_override(self, key: str, default: t.Any = None) -> t.Any:
        """
        Returns the corresponding value from the TOML file if found, otherwise
        the default value is returned instead.
        """
        try:
            toml_contents = self.get_toml_contents()
        except FileNotFoundError:
            logger.debug(f"{self.toml_file_name} wasn't found")
            return default
        else:
            value = toml_contents.get(key, ...)

            if value is ...:
                return default

            logger.debug(f"Loaded {key} from TOML file.")
            return value

    def validate(self):
        """
        Can be used to manually check the TOML file can be loaded::

            from piccolo.conf.overrides import OverrideLoader

            >>> OverrideLoader().validate()

        """
        try:
            self.get_toml_contents()
        except Exception as e:
            raise e
        else:
            print("Successfully loaded TOML file!")


DEFAULT_LOADER = OverrideLoader()


def get_override(key: str, default: t.Any = None) -> t.Any:
    """
    A convenience, instead of ``DEFAULT_LOADER.get_override``.
    """
    return DEFAULT_LOADER.get_override(key=key, default=default)
