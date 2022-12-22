import typing as t

from typing_extensions import assert_type

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

    assert_type(Band.from_dict(data={}), Band)

    assert_type(
        Band.update().run_sync(),
        t.List,
    )
