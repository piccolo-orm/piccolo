import typing as t

from typing_extensions import assert_type

from .example_apps.music.tables import Band

if t.TYPE_CHECKING:
    # Making sure the types are inferred correctly by MyPy.

    ###########################################################################
    # `objects`

    assert_type(
        Band.objects().run_sync(),
        t.List[Band],
    )

    assert_type(Band.objects().first().run_sync(), t.Optional[Band])

    assert_type(
        Band.objects().get(Band.name == "Pythonistas").run_sync(),
        t.Optional[Band],
    )

    assert_type(
        Band.objects().get_or_create(Band.name == "Pythonistas").run_sync(),
        Band,
    )

    ###########################################################################
    # `select`

    assert_type(Band.select().run_sync(), t.List[t.Dict[str, t.Any]])

    assert_type(
        Band.select().first().run_sync(), t.Optional[t.Dict[str, t.Any]]
    )

    ###########################################################################
    # `exists`

    assert_type(
        Band.exists().run_sync(),
        bool,
    )

    ###########################################################################
    # `table_exists`

    assert_type(
        Band.table_exists().run_sync(),
        bool,
    )

    ###########################################################################
    # `from_dict`

    assert_type(Band.from_dict(data={}), Band)

    ###########################################################################
    # `update`

    assert_type(
        Band.update().run_sync(),
        t.List[t.Any],
    )
