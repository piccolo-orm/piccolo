from __future__ import annotations
import itertools
import typing as t

import ujson as json

from piccolo.querystring import QueryString
from piccolo.utils.sync import run_sync

if t.TYPE_CHECKING:
    from piccolo.table import Table  # noqa


class Query(object):
    def __init__(
        self,
        table: t.Type[Table],
        base: QueryString = QueryString(""),
        *args,
        **kwargs,
    ) -> None:
        self.base = base
        self.table = table
        self._setup_delegates()

    def _setup_delegates(self):
        pass

    @property
    def engine_type(self) -> str:
        engine = self.table._meta.db
        if engine:
            return engine.engine_type
        else:
            raise ValueError("Engine isn't defined.")

    async def _process_results(self, results):
        if results:
            keys = results[0].keys()
            keys = [i.replace("$", ".") for i in keys]
            raw = [dict(zip(keys, i.values())) for i in results]
        else:
            raw = []

        if hasattr(self, "run_callback"):
            self.run_callback(raw)

        # TODO - I have multiple ways of modifying the final output
        # response_handlers, and output ...
        # Might try and merge them.
        raw = await self.response_handler(raw)

        output = getattr(self, "output_delegate", None)

        if output:
            if output._output.as_objects:
                # When using .first() we get a single row, not a list
                # of rows.
                if type(raw) is list:
                    raw = [self.table(**columns) for columns in raw]
                else:
                    raw = self.table(**raw)
            elif type(raw) is list:
                if output._output.as_list:
                    if len(raw[0].keys()) != 1:
                        raise ValueError(
                            "Each row returned more than one value"
                        )
                    else:
                        raw = list(itertools.chain(*[j.values() for j in raw]))
                if output._output.as_json:
                    raw = json.dumps(raw)

        return raw

    def _validate(self):
        """
        Override in any subclasses if validation needs to be run before
        executing a query - for example, warning a user if they're about to
        delete all the data from a table.
        """
        pass

    async def run(self, in_pool=True):
        self._validate()

        engine = self.table._meta.db
        if not engine:
            raise ValueError(
                f"Table {self.table._meta.tablename} has no db defined in _meta"
            )

        if len(self.querystrings) == 1:
            results = await engine.run_querystring(
                self.querystrings[0], in_pool=in_pool
            )
            return await self._process_results(results)
        else:
            responses = []
            # TODO - run in a transaction
            for querystring in self.querystrings:
                results = await engine.run_querystring(
                    querystring, in_pool=in_pool
                )
                responses.append(await self._process_results(results))
            return responses

    def run_sync(self, *args, **kwargs):
        """
        A convenience method for running the coroutine synchronously.
        """
        return run_sync(self.run(*args, **kwargs, in_pool=False))

    async def response_handler(self, response):
        """
        Subclasses can override this to modify the raw response returned by
        the database driver.
        """
        return response

    ###########################################################################

    @property
    def sqlite_querystrings(self) -> t.Sequence[QueryString]:
        raise NotImplementedError

    @property
    def postgres_querystrings(self) -> t.Sequence[QueryString]:
        raise NotImplementedError

    @property
    def default_querystrings(self) -> t.Sequence[QueryString]:
        raise NotImplementedError

    @property
    def querystrings(self) -> t.Sequence[QueryString]:
        """
        Calls the correct underlying method, depending on the current engine.
        """
        engine_type = self.engine_type
        if engine_type == "postgres":
            try:
                return self.postgres_querystrings
            except NotImplementedError:
                return self.default_querystrings
        elif engine_type == "sqlite":
            try:
                return self.sqlite_querystrings
            except NotImplementedError:
                return self.default_querystrings
        else:
            raise Exception(
                f"No querystring found for the {engine_type} engine."
            )

    ###########################################################################

    def __str__(self) -> str:
        return "; ".join([i.__str__() for i in self.querystrings])
