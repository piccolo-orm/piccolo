import asyncio
import itertools
import typing as t

import ujson as json

from ..utils.sync import run_sync

if t.TYPE_CHECKING:
    from table import Table  # noqa


class Query(object):

    def __init__(self, table: 'Table', base: str = '', *args,
                 **kwargs) -> None:
        self.base = base
        self.table = table
        super().__init__()

    async def run(self, as_dict=True, in_pool=True):
        engine = getattr(self.table.Meta, 'db', None)
        if not engine:
            raise ValueError(
                f'Table {self.table.Meta.tablename} has no db defined in Meta'
            )

        if in_pool:
            results = await engine.run_in_pool(self.__str__())
        else:
            results = await engine.run(self.__str__())

        if results:
            keys = results[0].keys()
            keys = [i.replace('$', '.') for i in keys]
            raw = [dict(zip(keys, i.values())) for i in results]
        else:
            raw = []

        if hasattr(self, 'run_callback'):
            self.run_callback(raw)

        # I have multiple ways of modifying the final output
        # response_handlers, and output ...
        # Might try and merge them.
        raw = self.response_handler(raw)

        output = getattr(self, '_output', None)

        if output:
            if output.as_objects:
                # When using .first() we get a single row, not a list
                # of rows.
                if type(raw) is list:
                    raw = [self.table(**columns) for columns in raw]
                else:
                    raw = self.table(**raw)
            elif type(raw) is list:
                if output.as_list:
                    if len(raw[0].keys()) != 1:
                        raise ValueError(
                            'Each row returned more than one value'
                        )
                    else:
                        raw = list(
                            itertools.chain(*[j.values() for j in raw])
                        )
                if output.as_json:
                    raw = json.dumps(raw)

        return raw

    def run_sync(self, *args, **kwargs):
        """
        A convenience method for running the coroutine synchronously.

        Might make it more sophisticated in the future, so not creating /
        tearing down connections, but instead running it in a separate
        process, and dispatching coroutines to it.
        """
        return run_sync(
            self.run(*args, **kwargs, in_pool=False)
        )

    def response_handler(self, response):
        """
        Subclasses can override this to modify the raw response returned by
        the database driver.
        """
        return response
