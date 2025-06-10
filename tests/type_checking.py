"""
Making sure the types are inferred correctly by MyPy.

Note: We need type annotations on the function, otherwise MyPy treats every
type inside the function as Any.
"""

from typing import TYPE_CHECKING, Any, Optional

from typing_extensions import assert_type

from piccolo.columns import ForeignKey, Varchar
from piccolo.testing.model_builder import ModelBuilder
from piccolo.utils.sync import run_sync

from .example_apps.music.tables import Band, Concert, Manager

if TYPE_CHECKING:

    async def objects() -> None:
        query = Band.objects()
        assert_type(await query, list[Band])
        assert_type(await query.run(), list[Band])
        assert_type(query.run_sync(), list[Band])

    async def objects_first() -> None:
        query = Band.objects().first()
        assert_type(await query, Optional[Band])
        assert_type(await query.run(), Optional[Band])
        assert_type(query.run_sync(), Optional[Band])

    async def get() -> None:
        query = Band.objects().get(Band.name == "Pythonistas")
        assert_type(await query, Optional[Band])
        assert_type(await query.run(), Optional[Band])
        assert_type(query.run_sync(), Optional[Band])

    async def foreign_key_reference() -> None:
        assert_type(Band.manager, ForeignKey[Manager])

    async def foreign_key_traversal() -> None:
        # Single level
        assert_type(Band.manager._.name, Varchar)
        # Multi level
        assert_type(Concert.band_1._.manager._.name, Varchar)

    async def get_related() -> None:
        band = await Band.objects().get(Band.name == "Pythonistas")
        assert band is not None
        manager = await band.get_related(Band.manager)
        assert_type(manager, Optional[Manager])

    async def get_related_multiple_levels() -> None:
        concert = await Concert.objects().first()
        assert concert is not None
        manager = await concert.get_related(Concert.band_1._.manager)
        assert_type(manager, Optional[Manager])

    async def get_or_create() -> None:
        query = Band.objects().get_or_create(Band.name == "Pythonistas")
        assert_type(await query, Band)
        assert_type(await query.run(), Band)
        assert_type(query.run_sync(), Band)

    async def select() -> None:
        query = Band.select()
        assert_type(await query, list[dict[str, Any]])
        assert_type(await query.run(), list[dict[str, Any]])
        assert_type(query.run_sync(), list[dict[str, Any]])

    async def select_first() -> None:
        query = Band.select().first()
        assert_type(await query, Optional[dict[str, Any]])
        assert_type(await query.run(), Optional[dict[str, Any]])
        assert_type(query.run_sync(), Optional[dict[str, Any]])

    async def select_list() -> None:
        query = Band.select(Band.name).output(as_list=True)
        assert_type(await query, list)
        assert_type(await query.run(), list)
        assert_type(query.run_sync(), list)
        # The next step would be to detect that it's list[str], but might not
        # be possible.

    async def select_as_json() -> None:
        query = Band.select(Band.name).output(as_json=True)
        assert_type(await query, str)
        assert_type(await query.run(), str)
        assert_type(query.run_sync(), str)

    async def exists() -> None:
        query = Band.exists()
        assert_type(await query, bool)
        assert_type(await query.run(), bool)
        assert_type(query.run_sync(), bool)

    async def table_exists() -> None:
        query = Band.table_exists()
        assert_type(await query, bool)
        assert_type(await query.run(), bool)
        assert_type(query.run_sync(), bool)

    async def from_dict() -> None:
        assert_type(Band.from_dict(data={}), Band)

    async def update() -> None:
        query = Band.update()
        assert_type(await query, list[Any])
        assert_type(await query.run(), list[Any])
        assert_type(query.run_sync(), list[Any])

    async def insert() -> None:
        # This is correct:
        Band.insert(Band())
        # This is an error:
        Band.insert(Manager())  # type: ignore

    async def model_builder() -> None:
        assert_type(await ModelBuilder.build(Band), Band)
        assert_type(ModelBuilder.build_sync(Band), Band)

    def run_sync_return_type() -> None:
        """
        Make sure `run_sync` returns the same type as the coroutine which is
        passed in.
        """

        async def my_func() -> str:
            return "hello"

        assert_type(run_sync(my_func()), str)
