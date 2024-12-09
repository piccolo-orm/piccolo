import inspect
import typing as t

from typing_extensions import Protocol

from piccolo.query.base import FrozenQuery
from piccolo.utils.sync import run_sync


class Runnable(Protocol):
    async def run(
        self, node: t.Optional[str] = None, in_pool: bool = True
    ): ...


QueryType = t.TypeVar("QueryType", bound=Runnable)
ResponseType = t.TypeVar("ResponseType")


class Proxy(t.Generic[QueryType, ResponseType]):
    def __init__(self, query: QueryType):
        self.query = query

    async def run(
        self,
        node: t.Optional[str] = None,
        in_pool: bool = True,
    ) -> ResponseType:
        return await self.query.run(node=node, in_pool=in_pool)

    def run_sync(self, *args, **kwargs) -> ResponseType:
        return run_sync(self.run(*args, **kwargs))

    def __await__(
        self,
    ) -> t.Generator[None, None, ResponseType]:
        """
        If the user doesn't explicity call .run(), proxy to it as a
        convenience.
        """
        return self.run().__await__()

    def freeze(self):
        self.query.freeze()
        return FrozenQuery(query=self)

    def __getattr__(self, name: str):
        """
        Proxy any attributes to the underlying query, so all of the query
        clauses continue to work.
        """
        attr = getattr(self.query, name)

        if inspect.ismethod(attr):
            # We do this to preserve the fluent interface.

            def proxy(*args, **kwargs):
                response = attr(*args, **kwargs)
                if isinstance(response, self.query.__class__):
                    self.query = response
                    return self
                else:
                    return response

            return proxy
        else:
            return attr

    def __str__(self) -> str:
        return self.query.__str__()
