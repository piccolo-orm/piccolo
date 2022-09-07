import typing as t

# Ironically, mypy complains about this - it does exist though:
from typing_extensions import assert_type  # type: ignore

from .example_apps.music.tables import Band

if t.TYPE_CHECKING:
    # Making sure the types are inferred correctly by MyPy.

    assert_type(Band.objects().first().run_sync(), t.Optional[Band])

    assert_type(
        Band.objects().get(Band.name == "Pythonistas").run_sync(),
        t.Optional[Band],
    )

    assert_type(
        Band.objects().get_or_create(Band.name == "Pythonistas").run_sync(),
        Band,
    )

    assert_type(
        Band.objects().run_sync(),
        t.List[Band],
    )

    assert_type(
        Band.exists().run_sync(),
        bool,
    )

    assert_type(
        Band.table_exists().run_sync(),
        bool,
    )

    assert_type(
        Band.update().run_sync(),
        bool,
    )
