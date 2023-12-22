"""
Making sure the types are inferred correctly by MyPy.

Note: We need type annotations on the function, otherwise MyPy treats every
type inside the function as Any.
"""

import typing as t

from typing_extensions import assert_type

from piccolo.columns import ForeignKey, Varchar
from piccolo.testing.model_builder import ModelBuilder

from .example_apps.music.tables import Band, Concert, Manager

if t.TYPE_CHECKING:

    async def objects() -> None:
        query = Band.objects()
        assert_type(await query, t.List[Band])
        assert_type(await query.run(), t.List[Band])
        assert_type(query.run_sync(), t.List[Band])

    async def objects_first() -> None:
        query = Band.objects().first()
        assert_type(await query, t.Optional[Band])
        assert_type(await query.run(), t.Optional[Band])
        assert_type(query.run_sync(), t.Optional[Band])

    async def get() -> None:
        query = Band.objects().get(Band.name == "Pythonistas")
        assert_type(await query, t.Optional[Band])
        assert_type(await query.run(), t.Optional[Band])
        assert_type(query.run_sync(), t.Optional[Band])

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
        assert_type(manager, t.Optional[Manager])

    async def get_or_create() -> None:
        query = Band.objects().get_or_create(Band.name == "Pythonistas")
        assert_type(await query, Band)
        assert_type(await query.run(), Band)
        assert_type(query.run_sync(), Band)

    async def select() -> None:
        query = Band.select()
        assert_type(await query, t.List[t.Dict[str, t.Any]])
        assert_type(await query.run(), t.List[t.Dict[str, t.Any]])
        assert_type(query.run_sync(), t.List[t.Dict[str, t.Any]])

    async def select_first() -> None:
        query = Band.select().first()
        assert_type(await query, t.Optional[t.Dict[str, t.Any]])
        assert_type(await query.run(), t.Optional[t.Dict[str, t.Any]])
        assert_type(query.run_sync(), t.Optional[t.Dict[str, t.Any]])

    async def select_list() -> None:
        query = Band.select(Band.name).output(as_list=True)
        assert_type(await query, t.List)
        assert_type(await query.run(), t.List)
        assert_type(query.run_sync(), t.List)
        # The next step would be to detect that it's t.List[str], but might not
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
        assert_type(await query, t.List[t.Any])
        assert_type(await query.run(), t.List[t.Any])
        assert_type(query.run_sync(), t.List[t.Any])

    async def insert() -> None:
        # This is correct:
        Band.insert(Band())
        # This is an error:
        Band.insert(Manager())  # type: ignore

    async def model_builder() -> None:
        assert_type(await ModelBuilder.build(Band), Band)
        assert_type(ModelBuilder.build_sync(Band), Band)
