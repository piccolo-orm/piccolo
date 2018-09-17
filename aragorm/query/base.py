import asyncio
import itertools
import typing as t

import asyncpg
import ujson as json

if t.TYPE_CHECKING:
    from table import Table  # noqa


class Query(object):

    def __init__(self, table: 'Table', base: str = '', *args,
                 **kwargs) -> None:
        self.base = base
        self.table = table
        super().__init__()

    async def run(self, as_dict=True, credentials=None):
        """
        Should use an engine.
        """
        if not credentials:
            credentials = getattr(self.table.Meta, 'db', None)
        if not credentials:
            raise ValueError('Table has no db defined in Meta')

        conn = await asyncpg.connect(**credentials)
        results = await conn.fetch(self.__str__())
        await conn.close()

        raw = [dict(i.items()) for i in results]

        if hasattr(self, 'run_callback'):
            self.run_callback(raw)

        # I have multiple ways of modifying the final output
        # response_handlers, and output ...
        # Might try and merge them.
        raw = self.response_handler(raw)

        output = getattr(self, '_output', None)

        if output:
            if output.as_objects:
                raw = [self.table(**columns) for columns in raw]
            elif type(raw) is list:
                if output.as_list:
                    if len(raw[0].keys()) != 1:
                        raise ValueError(
                            'Each row returned more than on value'
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
        return asyncio.run(
            self.run(*args, **kwargs)
        )

    def response_handler(self, response):
        """
        Subclasses can override this to modify the raw response returned by
        the database driver.
        """
        return response

    def _is_valid_column_name(self, column_name: str):
        if column_name.startswith('-'):
            column_name = column_name[1:]
        if column_name not in [i.name for i in self.table.Meta.columns]:
            raise ValueError(f"{column_name} isn't a valid column name")
